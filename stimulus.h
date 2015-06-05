#ifndef CT_STIMULUS_H
#define CT_STIMULUS_H

#include <rgb.h>
#include <dkl.h>
#include <fs.h>

namespace colortilt {


struct stimulus {

    stimulus() { }
    stimulus(double fg, double bg, float size, char side)
            : phi_fg(fg), phi_bg(bg), size(size), side(side) { }

    double phi_fg;
    double phi_bg;

    float size;
    char  side;

    static std::vector<stimulus> from_csv(const std::string &path);
    static bool to_csv(const std::vector<stimulus> &stimuli, std::ostream &stream);
};


std::vector<size_t> load_rnd_data(const fs::file &f);

}

#endif