

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


namespace gl = glue;

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



class ct_wnd : public gl::window {
public:
    ct_wnd(const std::string &title, gl::monitor m, iris::dkl &cspace)
            : window(title, m), colorspace(cspace) {
    }

    virtual void framebuffer_size_changed(glue::extent size) override;
    virtual void pointer_moved(glue::point pos) override;

    void render();

    iris::rgb fg = iris::rgb::cyan();
    iris::dkl &colorspace;
    gl::point cursor;
    float gain = 0.005;
    double phi = 0.0;
};

void ct_wnd::pointer_moved(gl::point pos) {
    gl::window::pointer_moved(pos);

    float x = cursor.x - pos.x;
    float y = cursor.y - pos.y;

    bool s = std::signbit(x*y);

    float length = hypot(x, y);

    cursor = pos;
    phi += length * gain * (s ? -1.0 : 1.0);

    fg = colorspace.iso_lum(phi, 0.1);
}

void ct_wnd::framebuffer_size_changed(gl::extent size) {
    gl::window::framebuffer_size_changed(size);
}


void ct_wnd::render() {

}

int main(int argc, char **argv) {

    iris::dkl::parameter params = iris::dkl::parameter::from_csv("rgb2sml.dat");
    params.print(std::cout);

    iris::rgb refpoint(0.65f, 0.65f, 0.65f);
    iris::dkl cspace(params, refpoint);

    if (!glfwInit()) {
        return -1;
    }

    gl::monitor moni = gl::monitor::monitors().back();
    ct_wnd wnd = ct_wnd("Color Tilt Experiment", moni, cspace);
    wnd.make_current_context();

    gl::extent phy = moni.physical_size();

    gl::shader vs;
    gl::shader fs;

    gl::program prg;

    gl::buffer bb;
    gl::vertex_array va;

    vs = gl::shader::make(vs_simple, GL_VERTEX_SHADER);
    fs = gl::shader::make(fs_simple, GL_FRAGMENT_SHADER);

    vs.compile();
    fs.compile();

    prg = gl::program::make();
    prg.attach({vs, fs});
    prg.link();

    std::vector<float> box = { 0.0f,  1.0f,
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

    while (! wnd.should_close()) {

        gl::extent fb = wnd.framebuffer_size();
        glm::mat4 projection = glm::ortho(0.f, phy.width, phy.height, 0.f);
        glm::mat4 tscale = glm::scale(glm::mat4(1), glm::vec3(phy.width*.5f, phy.height, 0));
        glm::mat4 ttrans = glm::translate(glm::mat4(1), glm::vec3(phy.width*.5f, 0.f, 0.0f));

        glm::mat4 mvp = projection * ttrans * tscale;

        glClearColor(0.5f, 0.5f, 0.5f, 1.0f);
        glClear(GL_COLOR_BUFFER_BIT);

        gl::color::rgba color(wnd.fg);

        prg.use();
        prg.uniform("plot_color", color);
        prg.uniform("viewport", mvp);

        va.bind();
        glDrawArrays(GL_TRIANGLES, 0, 6);

        va.unbind();
        prg.unuse();



        wnd.swap_buffers();
        glfwPollEvents();
    }

    glfwTerminate();
    return 0;
}