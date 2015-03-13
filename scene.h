#ifndef IRIS_SCENCE_H
#define IRIS_SCENCE_H

#include <iris.h>

#include <glue/basic.h>
#include <glue/window.h>
#include <glue/shader.h>
#include <glue/buffer.h>
#include <glue/arrays.h>

#include <dkl.h>
#include <misc.h>

#include <numeric>
#include <random>

namespace iris {

class rectangle {
public:
    void draw(glm::mat4 vp);
    void init();

    void configure(const iris::rgb &new_color);
    void configure(const glue::extent &new_size);
    glue::extent bounds() const;

private:
    iris::rgb color;
    glue::extent size;

    //gl
    glue::shader vs;
    glue::shader fs;

    glue::program prg;

    glue::buffer bb;
    glue::vertex_array va;
};


class checkerboard {
public:
    checkerboard(const iris::dkl &colorspace, double c);

    void init();
    void draw(glm::mat4 vp);
    void configure(glue::extent frame, glue::extent box_size);
    void reset_timer();
    double duration() const;

private:
    glue::extent size;
    std::random_device rd;
    std::mt19937 gen;
    std::uniform_int_distribution<size_t> dis;
    rectangle box;

    std::vector<iris::rgb> colors;
    double t_start;
};

}

#endif //IRIS_SCENCE_H
