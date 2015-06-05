#ifndef CT_STIMULUS_H
#define CT_STIMULUS_H

#include <rgb.h>
#include <dkl.h>
#include <fs.h>

namespace colortilt {


struct stimulus {

    stimulus() { }
    stimulus(double bg, double fg, float size, char side)
            : phi_bg(bg), phi_fg(fg), size(size), side(side) { }

    double phi_bg;
    double phi_fg;

    float size;
    char  side;

    static std::vector<stimulus> from_csv(const std::string &path);
    static bool to_csv(const std::vector<stimulus> &stimuli, std::ostream &stream);
};


std::vector<size_t> load_rnd_data(const fs::file &f);

}

#endif