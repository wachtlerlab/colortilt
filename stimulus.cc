#include "stimulus.h"

#include <csv.h>

namespace colortilt {

std::vector<stimulus> stimulus::from_csv(const std::string &path) {

    iris::csv_file fd(path);

    std::vector<stimulus> stimuli;
    for(const auto &rec : fd) {
        if (rec.is_empty() || rec.is_comment()) {
            continue;
        }

        if (rec.nfields() != 4) {
            throw std::runtime_error("Invalid CSV data");
        }

        stimulus s;
        s.phi_fg = rec.get_double(0);
        s.phi_bg = rec.get_double(1);
        s.size = rec.get_float(2);
        s.side = rec.get_char(3);

        stimuli.push_back(s);
    }

    return stimuli;
}

}