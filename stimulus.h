#ifndef CT_STIMULUS_H
#define CT_STIMULUS_H

#include <rgb.h>
#include <dkl.h>

namespace colortilt {


struct stimulus {

    stimulus() { }
    stimulus(double fg, double bg, float size) : phi_fg(fg), phi_bg(bg), size(size){ }

    double phi_fg;
    double phi_bg;

    float size;

    static std::vector<stimulus> from_csv(const std::string &path);
};


}

#endif