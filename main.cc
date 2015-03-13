

#include <iris.h>

#include <glue/basic.h>
#include <glue/window.h>
#include <glue/shader.h>
#include <glue/buffer.h>
#include <glue/arrays.h>

#include <glm/gtc/matrix_transform.hpp>

#include <iostream>
#include <dkl.h>
#include <misc.h>

#include <numeric>
#include <random>

#include <boost/program_options.hpp>


#include "stimulus.h"
#include "scene.h"

namespace gl = glue;
namespace ct = colortilt;

class ct_wnd : public gl::window {
public:
    ct_wnd(gl::monitor m, iris::dkl &cspace, const std::vector<ct::stimulus> &stimuli)
            : window("Color Tilt Experiment", m), colorspace(cspace), moni(m), stimuli(stimuli), board(cspace, 0.16) {
        make_current_context();
        box.init();
        board.init();

        stim_index = 0;

        cur_stim.phi_fg = 1.0f;
        cur_stim.phi_bg = 1.5f;

        gr_color = colorspace.reference_gray();
        intermission = false;

        std::vector<double> circ_phi = iris::linspace(0.0, 2*M_PI, 16);
        circ_rgb.resize(circ_phi.size());
        std::transform(circ_phi.cbegin(), circ_phi.cend(), circ_rgb.begin(), [&](const double p){
            iris::rgb crgb = colorspace.iso_lum(p, c_fg);
            uint8_t creport;
            iris::rgb res = crgb.clamp(&creport);
            if (creport != 0) {
                std::cerr << "[W] color clamped: " << crgb << " → " << res << " @ c: " << c_fg << std::endl;
            }
            return res;
        });

        disable_cursor();
    }

    virtual void framebuffer_size_changed(glue::extent size) override;
    virtual void pointer_moved(glue::point pos) override;
    virtual void key_event(int key, int scancode, int action, int mods) override;

    void render_stimulus();
    void render_checkerboard();
    void render();

    bool next_stimulus() {
        //todo: handle stimuli.empty?
        ct::stimulus cs = stimuli[stim_index++];
        cur_stim = cs;

        fg_color = colorspace.iso_lum(cs.phi_fg, c_fg);
        bg_color = colorspace.iso_lum(cs.phi_bg, c_bg);
        cu_color = colorspace.reference_gray();

        return stim_index < stimuli.size();
    }

    iris::rgb fg_color = iris::rgb::gray();
    iris::rgb bg_color = iris::rgb::gray();
    iris::rgb cu_color = iris::rgb::gray();
    iris::rgb gr_color;

    iris::dkl &colorspace;
    gl::monitor moni;
    const std::vector<ct::stimulus> &stimuli;
    size_t stim_index = 0;

    gl::point cursor;
    float gain = 0.001;
    double phi = 0.0;
    double c_fg = 0.16;
    double c_bg = 0.14;

    ct::stimulus cur_stim;
    std::vector<iris::rgb> circ_rgb;

    iris::rectangle box;
    iris::checkerboard board;

    bool intermission;
};

void ct_wnd::pointer_moved(gl::point pos) {
    gl::window::pointer_moved(pos);

    float x = cursor.x - pos.x;
    float y = cursor.y - pos.y;

    bool s = std::signbit(x*y);

    float length = std::hypot(x, y);

    cursor = pos;
    phi += length * gain * (s ? -1.0 : 1.0);
    phi = fmod(phi + (2.0f * M_PI), (2.0f * M_PI));

    cu_color = colorspace.iso_lum(phi, 0.16);
}

void ct_wnd::framebuffer_size_changed(gl::extent size) {
    gl::window::framebuffer_size_changed(size);
}

void ct_wnd::key_event(int key, int scancode, int action, int mods) {
    window::key_event(key, scancode, action, mods);

    if (key == GLFW_KEY_SPACE && action == GLFW_PRESS) {

        if (intermission) {
            return;
        }

        if (stim_index != 0) {
            std::cout << cur_stim.size << ", " << cur_stim.phi_bg << ", " << cur_stim.phi_fg << ", " << phi << std::endl;
        }
        bool keep_going = next_stimulus();
        should_close(!keep_going);
        intermission = true;
        board.reset_timer();
    }
}


void ct_wnd::render() {
    if (intermission) {
        render_checkerboard();

        double cb_time = board.duration();
        if (cb_time > 2.0f) {
            intermission = false;
        }

    } else {
        render_stimulus();
    }
}

void ct_wnd::render_checkerboard() {

    gl::extent phy = moni.physical_size();
    board.configure(phy, gl::extent(40.f, 40.f));
    glm::mat4 projection = glm::ortho(0.f, phy.width, phy.height, 0.f);
    board.draw(projection);

}

void ct_wnd::render_stimulus() {
    gl::extent phy = moni.physical_size();

    glm::mat4 projection = glm::ortho(0.f, phy.width, phy.height, 0.f);
    glm::mat4 ttrans = glm::translate(glm::mat4(1), glm::vec3(phy.width*.5f, 0.f, 0.0f));

    const float stim_size = cur_stim.size;

    const float center_x = phy.width * .25f - (stim_size * .5f);
    const float center_y = phy.height * .5f - (stim_size * .5f);

    glm::mat4 tr_center = glm::translate(glm::mat4(1), glm::vec3(center_x, center_y, 0.0f));

    glm::mat4 vp = projection * ttrans;

    glClearColor(gr_color.r, gr_color.b, gr_color.b, 1.0f);
    glClear(GL_COLOR_BUFFER_BIT);

    // background with color
    box.configure(gl::extent(phy.width * .5f, phy.height));
    box.configure(bg_color);
    box.draw(vp);

    // foreground with color
    box.configure(gl::extent(stim_size, stim_size));
    box.configure(fg_color);
    box.draw(vp * tr_center);

    // user choice on gray background
    box.configure(gl::extent(stim_size, stim_size));
    box.configure(cu_color);
    box.draw(projection * tr_center);
}

int main(int argc, char **argv) {
    namespace po = boost::program_options;

    std::string ca_path;
    std::string stim_path = "-";

    po::options_description opts("colortilt experiment");
    opts.add_options()
            ("help", "produce help message")
            ("calibration,c", po::value<std::string>(&ca_path)->required())
            ("stimuli,s", po::value<std::string>(&stim_path)->required());

    po::positional_options_description pos;
    pos.add("stimuli", 1);

    po::variables_map vm;
    try {
        po::store(po::command_line_parser(argc, argv).options(opts).positional(pos).run(), vm);
        po::notify(vm);
    } catch (const std::exception &e) {
        std::cerr << "Error while parsing commad line options: " << std::endl;
        std::cerr << "\t" << e.what() << std::endl;
        return 1;
    }

    if (vm.count("help") > 0) {
        std::cout << opts << std::endl;
        return 0;
    }

    if (stim_path == "-") {
        stim_path = "/dev/stdin";
    }

    std::vector<ct::stimulus> stimuli = ct::stimulus::from_csv(stim_path);
    iris::dkl::parameter params = iris::dkl::parameter::from_csv(ca_path);

    std::cerr << "Using rgb2sml calibration:" << std::endl;
    params.print(std::cerr);
    iris::rgb refpoint(iris::rgb::gray(0.66f));
    iris::dkl cspace(params, refpoint);

    if (!glfwInit()) {
        return -1;
    }

    gl::monitor moni = gl::monitor::monitors().back();
    ct_wnd wnd(moni, cspace, stimuli);

    while (! wnd.should_close()) {
        wnd.render();

        wnd.swap_buffers();
        glfwPollEvents();
    }

    glfwTerminate();
    return 0;
}