
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

namespace flicker {

struct setup {
    float   gray_level;
    float   stimulus_size;
    float   mouse_gain;
    double  contrast;
    gl::extent phy;
};

class flicker_wnd : public gl::window {
public:
    flicker_wnd(gl::monitor &m, iris::dkl &cs, setup s, const std::vector<double> &stim) :
            gl::window("Flicker", m), colorspace(cs), s(s), board(cs, s.contrast), phi(stim) {
        make_current_context();
        glfwSwapInterval(1);
        disable_cursor();

        wsize = s.phy;
        box.init();
        board.init();

        const float stim_size = s.stimulus_size;
        box.configure(gl::extent(stim_size, stim_size));

        glm::mat4 projection = glm::ortho(0.f, wsize.width, wsize.height, 0.f);

        const float center_x = wsize.width * .5f - (stim_size * .5f);
        const float center_y = wsize.height * .5f - (stim_size * .5f);

        glm::mat4 tr_center = glm::translate(glm::mat4(1), glm::vec3(center_x, center_y, 0.0f));
        mvp = projection * tr_center;

        stim_index = 0;
        fg_color = colorspace.iso_lum(phi[stim_index], s.contrast);;
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

        iris::rgb cur_color;
        if (draw_stim) {
            cur_color = fg_color;
        } else {
            cur_color = iris::rgb::gray(s.gray_level);
        }

        glClearColor(s.gray_level, s.gray_level, s.gray_level, 1.0f);
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
        if (key == GLFW_KEY_SPACE) {

            if (intermission) {
                return;
            }

            std::cout << phi[stim_index] << ", " << colorspace.reference_gray().r << std::endl;

            stim_index++;

            if (stim_index < phi.size()) {
                fg_color = colorspace.iso_lum(phi[stim_index], s.contrast);
                colorspace.reference_gray(iris::rgb::gray(s.gray_level));
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
        fg_color = colorspace.iso_lum(phi[stim_index], s.contrast);
    }

    virtual void pointer_moved(glue::point pos) override {
        float x = cursor.x - pos.x;
        float gain = s.mouse_gain;
        lum_change(x, gain);
        cursor = pos;
    }

private:
    gl::extent wsize;
    iris::dkl &colorspace;
    setup s;

    iris::rectangle box;
    iris::checkerboard board;

    std::vector<double> phi;
    size_t stim_index;

    iris::rgb fg_color;

    bool intermission;
    bool draw_stim;

    size_t nframes;

    glm::mat4 mvp;
    gl::point cursor;
};

} //flicker::

using namespace flicker;

template<typename T>
std::vector<T> repvec(const std::vector<T> &input, size_t n) {
    std::vector<T> res(n*input.size());

    auto output_iter = res.begin();
    for(size_t i = 0; i < n; i++) {
        std::advance(output_iter, input.size()*i);
        std::copy(input.cbegin(), input.cend(), output_iter);
    }

    return res;
}

int main(int argc, char **argv) {
    namespace po = boost::program_options;

    std::string ca_path;

    size_t N = 16;
    size_t R = 4;
    double contrast = 0.16;
    float width = 0.0f;
    float height = 0.0f;


    po::options_description opts("colortilt experiment");
    opts.add_options()
            ("help", "produce help message")
            ("number,n", po::value<size_t>(&N), "number of colors to sample [default=16")
            ("repetition,r", po::value<size_t>(&R), "number of repetitions [default=4]")
            ("contrast,C", po::value<double>(&contrast)->required())
            ("calibration,c", po::value<std::string>(&ca_path)->required())
            ("width,W", po::value<float>(&width))
            ("height,H", po::value<float>(&height));

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

    setup cfg;
    cfg.contrast = 0.16;
    cfg.stimulus_size = 40.f;
    cfg.mouse_gain = 0.00001;
    cfg.gray_level = 0.66f;

    gl::extent phy_size;
    if (width > 0.0f && height > 0.0f) {
        std::cerr << "Overwriting monitor size: " << width << "×" << height << std::endl;
        cfg.phy.width = width;
        cfg.phy.height = height;
    } else {
        cfg.phy = moni.physical_size();
    }

    iris::rgb refpoint(iris::rgb::gray(cfg.gray_level));
    iris::dkl cspace(params, refpoint);

    std::vector<double> phi = iris::linspace(0.0, 2 * M_PI, N);
    std::vector<double> stim = repvec(phi, R);

    if (stim.size() == 0) {
        std::cout << "# nothing to do" << std::endl;
        return 1;
    }


    flicker_wnd wnd(moni, cspace, cfg, stim);

    while (! wnd.should_close()) {
        wnd.render();
        glfwPollEvents();
    }

    glfwTerminate();
    return 0;
}
