

#include <iris.h>

#include <glue/basic.h>
#include <glue/window.h>
#include <glue/shader.h>
#include <glue/buffer.h>
#include <glue/arrays.h>

#include <glm/gtc/matrix_transform.hpp>

#include <dkl.h>
#include <misc.h>

#include <cstdlib>
#include <numeric>
#include <random>
#include <iostream>

#include <boost/program_options.hpp>

#include "stimulus.h"
#include "scene.h"

namespace colortilt {

struct response {

    response(const colortilt::stimulus &s, double phi, double duration)
            : stimulus(s), phi(phi), duration(duration) { }

    colortilt::stimulus stimulus;

    double phi;
    double duration;
};

}

namespace gl = glue;
namespace ct = colortilt;

class ct_wnd : public gl::window {
public:
    ct_wnd(const iris::data::display &display, iris::dkl &cspace, const std::vector<ct::stimulus> &stimuli,
           gl::extent phy_size, double c_fg, double c_bg)
            : window(display, "Color Tilt Experiment"), colorspace(cspace), stimuli(stimuli),
              c_fg(c_fg), c_bg(c_bg), board(cspace, c_fg), phy(phy_size) {
        make_current_context();
        glfwSwapInterval(1);

        box.init();
        board.init();

        stim_index = 0;

        cur_stim.phi_fg = 1.0f;
        cur_stim.phi_bg = 1.5f;

        gr_color = colorspace.reference_gray();
        intermission = false;

        disable_cursor();


    }

    const std::vector<ct::response>& responses() const {
        return resp;
    }

    virtual void framebuffer_size_changed(glue::extent size) override;
    virtual void pointer_moved(glue::point pos) override;
    virtual void key_event(int key, int scancode, int action, int mods) override;

    void render();

    void render_stimulus();
    void render_checkerboard();

    bool next_stimulus() {

        stim_index++;

        if (stim_index >= stimuli.size()) {
            return false;
        }

        //todo: handle stimuli.empty?
        ct::stimulus cs = stimuli[stim_index];
        cur_stim = cs;

        if (cs.phi_bg < 0) {
            bg_color = colorspace.reference_gray();
        } else {
            bg_color = colorspace.iso_lum(cs.phi_bg, c_bg);
        }

        fg_color = colorspace.iso_lum(cs.phi_fg, c_fg);

        double offset = (rand() % 2 == 0 ? 1.0f : -1.0f) * (M_PI/2.0 + 0.05 * phi);
        phi = fmod((cs.phi_fg + offset + 2.0f * M_PI), (2.0f * M_PI));
        cu_color = colorspace.iso_lum(phi, c_fg);

        return true;
    }

    void change_phi(double x, double gain) {
        phi += x * gain;
        phi = fmod(phi + (2.0f * M_PI), (2.0f * M_PI));
        cu_color = colorspace.iso_lum(phi, c_fg);
    }

    //member data

    iris::rgb fg_color = iris::rgb::gray();
    iris::rgb bg_color = iris::rgb::gray();
    iris::rgb cu_color = iris::rgb::gray();
    iris::rgb gr_color;

    iris::dkl &colorspace;
    const std::vector<ct::stimulus> &stimuli;
    size_t stim_index = 0;

    gl::point cursor;
    float cursor_gain = 0.0001;
    double phi = 0.0;
    double c_fg = 0.0;
    double c_bg = 0.0;

    ct::stimulus cur_stim;

    iris::rectangle box;
    iris::checkerboard board;

    gl::extent phy;
    bool intermission;

    std::vector<ct::response> resp;
};

void ct_wnd::pointer_moved(gl::point pos) {
    gl::window::pointer_moved(pos);

    float x = cursor.x - pos.x;
    change_phi(x, cursor_gain);
    cursor = pos;
}

void ct_wnd::framebuffer_size_changed(gl::extent size) {
    gl::window::framebuffer_size_changed(size);
}

void ct_wnd::key_event(int key, int scancode, int action, int mods) {
    window::key_event(key, scancode, action, mods);

    if (intermission) {
        return;
    }


    if (action != GLFW_PRESS) {
        return;
    }

    double gain = 2.25f;

    if (mods == GLFW_MOD_SHIFT) {
        gain *= 22.5f;
    } else if (mods == GLFW_MOD_CONTROL) {
        gain *= 1.0f;
    } else if (mods == GLFW_MOD_ALT) {
        gain *= .05f;
    }

    if (key == GLFW_KEY_SPACE) {

        if (stim_index != 0) {
            std::cerr << cur_stim.size << ", ";
            std::cerr << cur_stim.phi_bg << ", ";
            std::cerr << cur_stim.phi_fg << ", ";
            std::cerr << phi << ", ";
            std::cerr << cur_stim.side << std::endl;

            resp.emplace_back(cur_stim, phi, 0.0);
        }

        bool keep_going = next_stimulus();
        should_close(!keep_going);
        intermission = true;
        board.reset_timer();
    } else if (key == GLFW_KEY_RIGHT) {
        change_phi(M_PI / 180.0, gain);
    } else if (key == GLFW_KEY_LEFT) {
        change_phi(-1.0 * M_PI / 180.0, gain);
    } else if (key == GLFW_KEY_I) {
        std::cerr << phi << " " << cu_color;
    } else if (key == GLFW_KEY_R) {
        cursor_gain = 0.0001;
    } else if (key == GLFW_KEY_S) {
        cursor_gain *= 0.5;
    } else if (key == GLFW_KEY_D) {
        cursor_gain *= 2.0;
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
    const float stim_size = cur_stim.size;

    board.configure(phy, gl::extent(stim_size, stim_size));
    glm::mat4 projection = glm::ortho(0.f, phy.width, phy.height, 0.f);
    board.draw(projection);

}

void ct_wnd::render_stimulus() {

    gl::extent fb = framebuffer_size();
    glm::mat4 px2gl = glm::ortho(0.0f, fb.width, fb.height, 0.0f);
    glm::mat4 gl2px = glm::inverse(px2gl);

    glm::mat4 tpp = glm::translate(glm::mat4(1), glm::vec3(0.375f, 0.375f, 0.0f));

    glm::mat4 ppp = px2gl * tpp * gl2px;

    glm::mat4 projection = ppp * glm::ortho(0.f, phy.width, phy.height, 0.f);
    glm::mat4 ttrans = glm::translate(glm::mat4(1), glm::vec3(phy.width*.5f, 0.f, 0.0f));

    const float stim_size = cur_stim.size;

    const float center_x = phy.width * .25f - (stim_size * .5f);
    const float center_y = phy.height * .5f - (stim_size * .5f);

    glm::mat4 tr_center = glm::translate(glm::mat4(1), glm::vec3(center_x, center_y, 0.0f));

    glm::mat4 vp_stim = projection * ttrans;
    glm::mat4 vp_bg = projection;

    if (cur_stim.side == 'l') {
        using std::swap;
        swap(vp_bg, vp_stim);
    }

    glClearColor(gr_color.r, gr_color.b, gr_color.b, 1.0f);
    glClear(GL_COLOR_BUFFER_BIT);

    // background with color
    box.configure(gl::extent(phy.width * .5f, phy.height));
    box.configure(bg_color);
    box.draw(vp_stim);

    // foreground with color
    box.configure(gl::extent(stim_size, stim_size));
    box.configure(fg_color);
    box.draw(vp_stim * tr_center);

    // user choice on gray background
    box.configure(gl::extent(stim_size, stim_size));
    box.configure(cu_color);
    box.draw(vp_bg * tr_center);
}


int main(int argc, char **argv) {
    namespace po = boost::program_options;

    std::string stim_path = "-";
    float gray_level = -1;
    double c_fg = 0.f;
    double c_bg = 0.f;

    std::string sid = "";

    po::options_description opts("colortilt experiment");
    opts.add_options()
            ("help", "produce help message")
            ("c-fg", po::value<double>(&c_fg)->required())
            ("c-bg", po::value<double>(&c_bg)->required())
            ("gray", po::value<float>(&gray_level), "reference gray [default=read from rgb2lms]")
            ("stimuli,s", po::value<std::string>(&stim_path)->required())
            ("subject,S", po::value<std::string>(&sid)->required());

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

    // the display env
    iris::data::store store = iris::data::store::default_store();
    std::string mdev = store.default_monitor();

    iris::data::monitor moni = store.load_monitor(mdev);
    iris::data::monitor::mode mode = moni.default_mode;
    iris::data::display display = store.make_display(moni, mode, "gl");
    iris::data::rgb2lms rgb2lms = store.load_rgb2lms(display);

    iris::dkl::parameter params = rgb2lms.dkl_params;
    gl::extent phy_size(rgb2lms.width, rgb2lms.height);

    std::vector<ct::stimulus> stimuli = ct::stimulus::from_csv(stim_path);

    if (stimuli.size() == 0) {
        std::cerr << "[E] No stimuli to present!!" << std::endl;
        return -2;
    }

    if (gray_level < 0) {
        gray_level = rgb2lms.gray_level;
    } else {
        std::cerr << "[W] overriding gray-level: ";
        std::cerr << gray_level << "* " << rgb2lms.gray_level;
        std::cerr << std::endl;
    }

    std::cerr << "[I] Stimuli N: " << stimuli.size() << std::endl;
    std::cerr << "[I] contrast fg: " << c_fg << std::endl;
    std::cerr << "[I] contrast bg: " << c_bg << std::endl;
    std::cerr << "[I] gray-level: " << gray_level << std::endl;

    std::cerr << "[I] rgb2sml calibration:" << std::endl;
    params.print(std::cerr);
    iris::rgb refpoint(iris::rgb::gray(gray_level));
    iris::dkl cspace(params, refpoint);

    std::vector<iris::data::subject> hits = store.find_subjects(sid);
    if (hits.empty()) {
        std::cerr << "Coud not find subject [" << sid << "]" << std::endl;
    } else if (hits.size() > 1) {
        std::cerr << "Ambigous subject string (> 1 hits): " << std::endl;
        for (const auto &s : hits) {
            std::cerr << "\t" << s.initials << std::endl;
        }
    }

    const iris::data::subject subject = hits.front(); // size() == 1 asserted
    iris::data::isoslant iso = store.load_isoslant(subject);
    cspace.iso_slant(iso.dl, iso.phi);

    std::cerr << "[I] subject: " << subject.identifier() << std::endl;
    std::cerr << "[I] isoslant: [dl: " << iso.dl << ", " << iso.phi << "]" << std::endl;


    if (!glfwInit()) {
        return -1;
    }

    std::srand(31337); // so random, very wow!

    ct_wnd wnd(display, cspace, stimuli, phy_size, c_fg, c_bg);

    while (! wnd.should_close()) {
        wnd.render();

        wnd.swap_buffers();
        glfwPollEvents();
    }

    //
    std::stringstream outstr;
    outstr << "size, bg, fg, phi, side, duration";
    for (const auto &resp : wnd.responses()) {
        outstr << std::endl;
        outstr << resp.stimulus.size << ", ";
        outstr << resp.stimulus.phi_bg << ", ";
        outstr << resp.stimulus.phi_fg << ", ";
        outstr << resp.phi << ", ";
        outstr << resp.stimulus.side << ", ";
        outstr << resp.duration;
    }

    std::cout << outstr.str() << std::endl;

    glfwTerminate();
    return 0;
}