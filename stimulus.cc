#include "stimulus.h"

#include <csv.h>
#include <fs.h>

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


std::vector<size_t> load_rnd_data(const fs::file &f) {
    typedef iris::csv_iterator<std::string::const_iterator> csv_siterator;

    std::string data = f.read_all();
    bool is_header = true;

    std::vector<size_t> rnddata;

    for (auto iter = csv_siterator(data.cbegin(), data.cend(), ',');
         iter != csv_siterator();
         ++iter) {
        auto rec = *iter;

        if (rec.is_comment() || rec.is_empty()) {
            continue;
        }

        if (is_header) {
            is_header = false;
            continue;
        }

        if (rec.nfields() != 1) {
            throw std::runtime_error("Invalid CSV data for rnd file");
        }

        rnddata.push_back(rec.get_size_t(0));
    }

    return rnddata;
}


}