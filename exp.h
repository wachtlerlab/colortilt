
#ifndef CT_EXPERIMENT_H
#define CT_EXPERIMENT_H

#include <iris.h>

#include <rgb.h>
#include <dkl.h>
#include <fs.h>
#include <data.h>

#include <yaml-cpp/yaml.h>

#include "stimulus.h"

namespace colortilt {

struct response {

    response(const colortilt::stimulus &s, double phi, double duration, double phi_start)
            : stimulus(s), phi(phi), duration(duration), phi_start(phi_start) { }

    colortilt::stimulus stimulus;

    double phi;
    double duration;
    double phi_start;
};

struct session {
    std::string stim;
    std::string rnd;

    static session from_string(const std::string &str);

    std::string name() const {
        return stim + "@" + rnd;
    }

    explicit operator bool() const {
        return !stim.empty() && !rnd.empty();
    }
};

struct trail {

    std::string stim;
    std::string rnd;

    std::string name() const {
        return stim + "@" + rnd;
    }

    static trail from_string(const std::string &str);
};

struct experiment {
    double c_fg;
    double c_bg;
    double cursor_gain;

    std::string data_path;
    std::string stim_path;
    std::string sess_path;

    static experiment from_yaml(const fs::file &path);
    static fs::file find_file(const std::string &additional_path);

    fs::file data_dir() const;
    fs::file stim_dir() const;
    fs::file sess_dir() const;
    fs::file resp_dir(const iris::data::subject &sub) const;

    fs::file session_file(const iris::data::subject &s) const;
    fs::file stim_file(const session &s) const;
    fs::file rnd_file(const session &s) const;
    fs::file resp_file(const session &ses, const iris::data::subject &sub, const std::string &prefix = "") const;

    std::vector<std::string> subjects() const;

    std::vector<session> load_sessions(const iris::data::subject &sub) const;
    std::vector<trail> list_trails(const iris::data::subject &sub) const;

    session next_session(const iris::data::subject &sub) const;



    //utility
    fs::file make_file(const std::string &path) const;

    // runtime data
    fs::file source_file;
};


} // colortilt::

#endif //CT_EXPERIMENT_H
