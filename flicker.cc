
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

#include "scene.h"

#include <iostream>

namespace gl = glue;

class flicker_wnd : public gl::window {
public:
    flicker_wnd(gl::monitor &m, iris::dkl &cs, double c) :
            gl::window("Flicker", m), colorspace(cs), c(c), board(cs, c) {
        make_current_context();
        glfwSwapInterval(1);
        disable_cursor();
        float stim_size = 40;

        wsize = m.physical_size();
        box.init();
        board.init();

        box.configure(gl::extent(stim_size, stim_size));

        glm::mat4 projection = glm::ortho(0.f, wsize.width, wsize.height, 0.f);

        const float center_x = wsize.width *  .5f - (stim_size * .5f);
        const float center_y = wsize.height * .5f - (stim_size * .5f);

        glm::mat4 tr_center = glm::translate(glm::mat4(1), glm::vec3(center_x, center_y, 0.0f));
        mvp = projection * tr_center;

        phi = iris::linspace(0.0, 2*M_PI, 8);
        stim_index = 0;

        fg_color = colorspace.iso_lum(phi[stim_size], c);
        intermission = false;
    }

    void render() {
        nframes++;

        if (nframes == 60) {
            nframes = 0;
        }

        // Assumes 60 Hz
        if (nframes % 3 == 0) {

            draw_stim = !draw_stim;
        }

        if(draw_stim) {
            cur_color = fg_color;
        } else {
            cur_color = iris::rgb::gray(0.6f);
        }

        glClearColor(0.6f, 0.6f, 0.6f, 1.0f);
        glClear(GL_COLOR_BUFFER_BIT);

        box.configure(cur_color);
        box.draw(mvp);

        swap_buffers();
    }

    virtual void key_event(int key, int scancode, int action, int mods) override {
        window::key_event(key, scancode, action, mods);

        if (action != GLFW_PRESS) {
            return;
        }

        float gain = mods == GLFW_MOD_SHIFT ? .5f : 0.01f;
        if (key == GLFW_KEY_SPACE ) {

            if (intermission) {
                return;
            }

            stim_index++;

            if (stim_index < phi.size()) {
                fg_color = colorspace.iso_lum(phi[stim_index], c);
                colorspace.reference_gray(iris::rgb::gray(0.66f));
            } else {
                should_close(true);
            }

        } else if (key == GLFW_KEY_RIGHT) {
            lum_change(.1f, gain);
        } else if (key == GLFW_KEY_LEFT) {
            lum_change(-.1f, gain);
        }
    }

    void lum_change(float delta, float gain) {
        iris::rgb gray = colorspace.reference_gray();
        gray = iris::rgb::gray(gray.r + delta * gain).clamp();
        colorspace.reference_gray(gray);
        fg_color = colorspace.iso_lum(phi[stim_size], c);
    }

    virtual void pointer_moved(glue::point pos) override {
        float x = cursor.x - pos.x;
        float gain = 0.00001;
        lum_change(x, gain);
        cursor = pos;
    }

private:
    gl::extent wsize;
    iris::dkl &colorspace;
    double c;

    iris::rectangle box;
    iris::checkerboard board;

    std::vector<double> phi;
    size_t stim_index;

    iris::rgb fg_color;
    iris::rgb cur_color;

    bool intermission;
    bool draw_stim;

    size_t nframes;

    float stim_size;
    glm::mat4 mvp;
    gl::point cursor;
};

int main(int argc, char **argv) {
    namespace po = boost::program_options;

    std::string ca_path;

    po::options_description opts("colortilt experiment");
    opts.add_options()
            ("help", "produce help message")
            ("calibration,c", po::value<std::string>(&ca_path)->required());

    po::positional_options_description pos;

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

    if (!glfwInit()) {
        return -1;
    }

    gl::monitor moni = gl::monitor::monitors().back();
    iris::dkl::parameter params = iris::dkl::parameter::from_csv(ca_path);

    std::cerr << "Using rgb2sml calibration:" << std::endl;
    params.print(std::cerr);
    iris::rgb refpoint(iris::rgb::gray(0.66f));
    iris::dkl cspace(params, refpoint);

    flicker_wnd wnd(moni, cspace, 0.16);

    while (! wnd.should_close()) {
        wnd.render();
        glfwPollEvents();
    }

    glfwTerminate();
    return 0;
}
