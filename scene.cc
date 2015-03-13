
#include "scene.h"

#include <glm/gtc/matrix_transform.hpp>

namespace gl = glue;

namespace iris {



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


void rectangle::draw(glm::mat4 vp) {
    glm::mat4 tscale = glm::scale(glm::mat4(1), glm::vec3(size.width, size.height, 0));

    glm::mat4 mvp = vp * tscale;

    gl::color::rgba gl_color(color);

    prg.use();
    prg.uniform("plot_color", gl_color);
    prg.uniform("viewport", mvp);

    va.bind();
    glDrawArrays(GL_TRIANGLES, 0, 6);

    va.unbind();
    prg.unuse();
}

void rectangle::init() {
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

void rectangle::configure(const iris::rgb &new_color) {
    color = new_color;
}

void rectangle::configure(const glue::extent &new_size) {
    size = new_size;
}

glue::extent rectangle::bounds() const {
    return size;
}

//*****************************************************************************


checkerboard::checkerboard(const iris::dkl &colorspace, double c)
        : rd(), gen(rd()), dis(0, 15) {
    std::vector<double> circ_phi = iris::linspace(0.0, 2*M_PI, 16);
    colors.resize(circ_phi.size());
    std::transform(circ_phi.cbegin(), circ_phi.cend(), colors.begin(), [&](const double p){
        iris::rgb crgb = colorspace.iso_lum(p, c);
        uint8_t creport;
        iris::rgb res = crgb.clamp(&creport);
        if (creport != 0) {
            std::cerr << "[W] color clamped: " << crgb << " → " << res << " @ c: " << c << std::endl;
        }
        return res;
    });
}

void checkerboard::init() {
    box.init();
}

void checkerboard::draw(glm::mat4 vp) {
    for (float x = 0.f; x < size.width; x += box.bounds().width) {
        for(float y = 0.f; y < size.height; y += box.bounds().height) {
            glm::mat4 ttrans = glm::translate(glm::mat4(1), glm::vec3(x, y, 0.0f));

            box.configure(colors[dis(gen)]);
            box.draw(vp * ttrans);
        }
    }
}

void checkerboard::configure(glue::extent frame, glue::extent box_size) {
    size = frame;
    box.configure(box_size);
}

void checkerboard::reset_timer() {
    t_start = glfwGetTime();
}

double checkerboard::duration() const {
    double t_now = glfwGetTime();
    return t_now - t_start;
}


}