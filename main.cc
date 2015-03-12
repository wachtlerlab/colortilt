

#include <iris.h>

#include <glue/basic.h>
#include <glue/window.h>
#include <glue/shader.h>
#include <glue/buffer.h>
#include <glue/arrays.h>

#include <glm/gtc/matrix_transform.hpp>

#include <iostream>
#include <dkl.h>

#include <numeric>

#include <boost/program_options.hpp>

#include "stimulus.h""

namespace gl = glue;
namespace ct = colortilt;

static const char vs_simple[] = R"SHDR(
#version 330

layout(location = 0) in vec2 pos;

uniform mat4 viewport;

void main()
{
    gl_Position = viewport * vec4(pos, 0.0, 1.0);
}
)SHDR";

static const char fs_simple[] = R"SHDR(
#version 330

out vec4 finalColor;
uniform vec4 plot_color;

void main() {
    finalColor = plot_color;
}
)SHDR";


class rectangle {
public:
    void draw(glm::mat4 vp) {
        glm::mat4 tscale = glm::scale(glm::mat4(1), glm::vec3(size.width, size.height, 0));

        glm::mat4 mvp = vp * tscale;

        glClearColor(0.5f, 0.5f, 0.5f, 1.0f);

        gl::color::rgba gl_color(color);

        prg.use();
        prg.uniform("plot_color", gl_color);
        prg.uniform("viewport", mvp);

        va.bind();
        glDrawArrays(GL_TRIANGLES, 0, 6);

        va.unbind();
        prg.unuse();
    }

    void init() {

        vs = gl::shader::make(vs_simple, GL_VERTEX_SHADER);
        fs = gl::shader::make(fs_simple, GL_FRAGMENT_SHADER);

        vs.compile();
        fs.compile();

        prg = gl::program::make();
        prg.attach({vs, fs});
        prg.link();


        std::vector<float> box = {
                0.0f,  1.0f,
                0.0f, 0.0f,
                1.0f, 0.0f,

                1.0f,  1.0f,
                0.0f,  1.0f,
                1.0f, 0.0f};

        bb = gl::buffer::make();
        va = gl::vertex_array::make();

        bb.bind();
        va.bind();

        bb.data(box);

        glEnableVertexAttribArray(0);
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 0, nullptr);

        glBindBuffer(GL_ARRAY_BUFFER, 0);
        glBindVertexArray(0);

        bb.unbind();
        va.unbind();
    }

    void configure(const iris::rgb &new_color) {
        color = new_color;
    }

    void configure(const gl::extent &new_size) {
        size = new_size;
    }

    gl::extent bounds() const {
        return size;
    }

private:
    iris::rgb color;
    gl::extent size;

    //gl
    gl::shader vs;
    gl::shader fs;

    gl::program prg;

    gl::buffer bb;
    gl::vertex_array va;
};



class ct_wnd : public gl::window {
public:
    ct_wnd(const std::string &title, gl::monitor m, iris::dkl &cspace)
            : window(title, m), colorspace(cspace), moni(m) {
        make_current_context();
        box_bg.init();
        box_fg.init();
        box_user.init();

        cur_stim.fg = colorspace.iso_lum(1.0f, 0.16);
        cur_stim.bg = colorspace.iso_lum(1.5f, 0.15);

    }

    virtual void framebuffer_size_changed(glue::extent size) override;
    virtual void pointer_moved(glue::point pos) override;
    virtual void key_event(int key, int scancode, int action, int mods) override;

    void render();

    iris::rgb fg = iris::rgb::cyan();
    iris::dkl &colorspace;
    gl::monitor moni;
    gl::point cursor;
    float gain = 0.005;
    double phi = 0.0;

    ct::stimulus cur_stim;

    rectangle box_bg;
    rectangle box_fg;
    rectangle box_user;
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

    fg = colorspace.iso_lum(phi, 0.16);
}

void ct_wnd::framebuffer_size_changed(gl::extent size) {
    gl::window::framebuffer_size_changed(size);
}

void ct_wnd::key_event(int key, int scancode, int action, int mods) {
    window::key_event(key, scancode, action, mods);

    if (key == GLFW_KEY_SPACE && action == GLFW_PRESS) {
        std::cout << phi << std::endl;
    }
}

void ct_wnd::render() {
    gl::extent phy = moni.physical_size();

    glm::mat4 projection = glm::ortho(0.f, phy.width, phy.height, 0.f);
    glm::mat4 ttrans = glm::translate(glm::mat4(1), glm::vec3(phy.width*.5f, 0.f, 0.0f));

    const float box_size = 40.f;

    const float center_x = phy.width * .25f - (box_size * .5f);
    const float center_y = phy.height * .5f - (box_size * .5f);

    glm::mat4 tr_center = glm::translate(glm::mat4(1), glm::vec3(center_x, center_y, 0.0f));

    glm::mat4 vp = projection * ttrans;

    glClearColor(0.66f, 0.66f, 0.66f, 1.0f);
    glClear(GL_COLOR_BUFFER_BIT);

    // background with color
    box_bg.configure(gl::extent(phy.width * .5f, phy.height));
    box_bg.configure(cur_stim.fg);
    box_bg.draw(vp);

    //
    box_fg.configure(gl::extent(box_size, box_size));
    box_fg.configure(cur_stim.bg);
    box_fg.draw(vp * tr_center);

    //
    box_user.configure(gl::extent(box_size, box_size));
    box_user.configure(fg);
    box_user.draw(projection * tr_center);

}

int main(int argc, char **argv) {
    namespace po = boost::program_options;

    std::string ca_path;

    po::options_description opts("colortilt experiment");
    opts.add_options()
            ("help", "produce help message")
            ("calibration,c", po::value<std::string>(&ca_path)->required());

    po::positional_options_description pos;
    pos.add("cone-fundamentals", 1);

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

    iris::dkl::parameter params = iris::dkl::parameter::from_csv(ca_path);
    std::cerr << "Using rgb2sml calibration:" << std::endl;
    params.print(std::cerr);
    iris::rgb refpoint(0.65f, 0.65f, 0.65f);
    iris::dkl cspace(params, refpoint);

    if (!glfwInit()) {
        return -1;
    }

    gl::monitor moni = gl::monitor::monitors().back();
    ct_wnd wnd = ct_wnd("Color Tilt Experiment", moni, cspace);

    while (! wnd.should_close()) {
        wnd.render();

        wnd.swap_buffers();
        glfwPollEvents();
    }

    glfwTerminate();
    return 0;
}