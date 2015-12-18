#include "exp.h"
#include <misc.h>

namespace colortilt {

session session::from_string(const std::string &str) {
    size_t pos = str.find("@");
    if (pos == std::string::npos) {
        throw std::runtime_error("Invalid session format");
    }

    session s;
    s.stim = str.substr(0, pos);
    s.rnd = str.substr(pos+1);

    return s;
}


trail trail::from_string(const std::string &str) {

    trail t;
    size_t pos = str.find("@");
    if (pos != std::string::npos) {
        t.stim = str.substr(0, pos);
        t.rnd = str.substr(pos+1);
    } else {
        t.stim = str;
        t.rnd = "";
    }

    return t;
}

experiment experiment::from_yaml(const fs::file &path) {
    std::string data = path.read_all();
    YAML::Node doc = YAML::Load(data);
    YAML::Node root = doc["colortilt"];

    colortilt::experiment exp;
    exp.c_fg = root["contrast"]["fg"].as<double>();
    exp.c_bg = root["contrast"]["bg"].as<double>();
    exp.data_path = root["data-path"].as<std::string>();
    exp.stim_path = root["stim-path"].as<std::string>();
    exp.sess_path = root["sess-path"].as<std::string>();
    exp.cursor_gain = root["cursor-gain"].as<double>();

    exp.source_file = path;
    return exp;
}


fs::file experiment::find_file(const std::string &name, const std::string &additional_path) {

    std::vector<fs::file> known_files = {
            fs::file(name + additional_path),
            fs::file(name + ".experiment"),
            fs::file("~/" + name + ".experiment"),
            fs::file("~/experiments/" + name + ".experiment"),
            fs::file("~/experiments/" + name + "/experiment")
    };

    std::cerr << "[D] Looking for exp file in: " << std::endl;
    for (fs::file &f : known_files) {
        std::cerr << f.path() << std::endl;
        if (f.exists()) {
            return f;
        }
    }

    return fs::file();
}


fs::file experiment::make_file(const std::string &path) const {
    if (path.empty()) {
        return fs::file();
    }

    if (fs::file::path_is_absolute(path)) {
        return fs::file(path);
    }

    // handle relative paths to exp source file
    if (path[0] == '.') {
        return source_file.parent().child(path);
    }

    return fs::file(path);
}

fs::file experiment::data_dir() const {
    return make_file(data_path);
}

fs::file experiment::stim_dir() const {
    return make_file(stim_path);
}

fs::file experiment::sess_dir() const {
    return make_file(sess_path);
}

fs::file experiment::resp_dir(const iris::data::subject &sub) const {
    fs::file base = data_dir();
    return base.child(sub.identifier());
}

fs::file experiment::stim_file(const session &s) const {
    fs::file base = stim_dir();
    return base.child(s.stim + ".stm");
}

fs::file experiment::rnd_file(const session &s) const {
    fs::file base = stim_dir();
    return base.child(s.rnd + ".rnd");
}

fs::file experiment::session_file(const iris::data::subject &s) const {
    fs::file base = sess_dir();
    fs::file session_file = base.child(s.identifier() + ".sessions");
    return session_file;
}

fs::file experiment::resp_file(const session &ses, const iris::data::subject &sub, const std::string &prefix) const {
    fs::file sub_base = resp_dir(sub);
    fs::file resp_file = sub_base.child(prefix + ses.name() + ".dat");
    return resp_file;
}


std::vector<std::string> experiment::subjects() const {
    fs::file base = sess_dir();

    std::vector<fs::file> res;
    std::copy_if(base.children().begin(), base.children().end(),
                 std::back_inserter(res), fs::fn_matcher("*.sessions"));

    std::vector<std::string> subjects;
    std::transform(res.begin(), res.end(), std::back_inserter(subjects), [](const fs::file &f){
        std::string name, ext;
        std::tie(name, ext) = f.splitext();
        return name;
    });

    return subjects;
}

std::vector<session> experiment::load_sessions(const iris::data::subject &sub) const {
    fs::file session_fn = session_file(sub);

    if (! session_fn.exists()) {
        std::cerr << "[W] EEXIST: " << session_fn.path() << std::endl;
        return std::vector<session>();
    }

    std::string data = session_fn.read_all();

    YAML::Node doc = YAML::Load(data);
    YAML::Node root = doc["sessions"];

    std::vector<session> sessions;
    std::transform(root.begin(), root.end(), std::back_inserter(sessions),
                   [](const YAML::Node &cn) {
                       return session::from_string(cn.as<std::string>());
                   });

    return sessions;
}


std::vector<trail> experiment::list_trails(const iris::data::subject &sub) const {
    std::string timebase = iris::make_timestamp();
    const size_t ts_size = timebase.size();

    fs::file target = resp_dir(sub);

    std::vector<fs::file> dat_files;
    std::copy_if(target.children().begin(), target.children().end(),
                 std::back_inserter(dat_files), fs::fn_matcher("*.dat"));

    std::vector<colortilt::trail> trails;
    std::transform(dat_files.begin(), dat_files.end(),
                   std::back_inserter(trails),
                   [ts_size](const fs::file &f) {
                       std::string name = f.name();
                       size_t name_len = name.size();
                       name_len -= (ts_size + 5);
                       std::string nid =  name.substr(ts_size + 1, name_len);
                       return colortilt::trail::from_string(nid);
                   });

    return trails;
}

session experiment::next_session(const iris::data::subject &sub) const {
    std::string timebase = iris::make_timestamp();
    const size_t ts_size = timebase.size();

    fs::file target = resp_dir(sub);
    std::cerr << "[I] subject data dir: " << target.path() << std::endl;

    std::vector<fs::file> dat_files;
    std::copy_if(target.children().begin(), target.children().end(),
                 std::back_inserter(dat_files), fs::fn_matcher("*.dat"));

    std::vector<std::string> dat_names;
    std::transform(dat_files.begin(), dat_files.end(),
                   std::back_inserter(dat_names),
                   [ts_size](const fs::file &f) {
                       std::string name = f.name();
                       size_t name_len = name.size();
                       name_len -= (ts_size + 5);
                       return name.substr(ts_size + 1, name_len);
                   });

    std::cerr << "[I] checking sessions: " << std::endl;
    std::cerr << "\t key: # = responses / № counts of stim pattern" << std::endl;

    for (std::string name : dat_names) {
        std::cerr << "\t Found " << name << std::endl;
    }

    std::vector<session> sessions = load_sessions(sub);
    for (auto it = sessions.begin(); it != sessions.end(); ++it) {
        const session &se = *it;
        fs::file rsf = resp_file(se, sub);
        std::string rsf_name = se.name();
        // it + 1 because for reverse_iter (r) from iter (i): &*r == &*(i-1)
        auto riter = std::reverse_iterator<std::vector<session>::iterator>(it+1);
        auto n_stim = std::count_if(riter, sessions.rend(),
                                    [&rsf_name](const session &cur_session) {
                                        return rsf_name == cur_session.name();
                                    });

        auto n_resp = std::count_if(dat_names.begin(), dat_names.end(),
                                    [&rsf_name](const std::string &cur_name) {
                                        return rsf_name == cur_name;
                                    });

        std::cerr << "\t [" << rsf.name() << "] #" << n_resp << "/" << n_stim << "№";
        bool needs_doing = n_resp < n_stim;
        std::cerr << (needs_doing ? u8" *" : u8" ✓") << std::endl;

        if (needs_doing) {
            return se;
        }
    }

    return colortilt::session();
}

}