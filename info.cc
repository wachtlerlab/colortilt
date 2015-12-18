
#include "exp.h"

#include <stdexcept>
#include <set>

struct session_info {

    std::string name;

    std::vector<std::string> todo;
    std::vector<std::string> done;
};

struct session_set {

    session_info& add(const colortilt::session &info);
    session_info& add(const colortilt::trail &trail);
    std::vector<session_info> sessions;
};


session_info &session_set::add(const colortilt::session &info) {

    for (session_info &i : sessions) {
        if (i.name == info.stim) {
            i.todo.push_back(info.rnd);
            return i;
        }
    }

    session_info nfo;
    nfo.name = info.stim;
    nfo.todo = std::vector<std::string>{info.rnd};
    sessions.push_back(nfo);
    return sessions.back();
}

session_info &session_set::add(const colortilt::trail &trail) {

    for (session_info &i : sessions) {
        if (i.name == trail.stim) {
            i.done.push_back(trail.rnd);
            return i;
        }
    }

    session_info nfo;
    nfo.name = trail.stim;
    nfo.done = std::vector<std::string>{trail.rnd};
    sessions.push_back(nfo);
    return sessions.back();
}




int main(int argc, char **argv) {

    try {
        iris::data::store store = iris::data::store::default_store();

        std::string name = "";
        if (argc > 1) {
            name = argv[1];
        }

        std::string baseloc = "";
        if (argc > 2) {
            baseloc = argv[2];
        }


        // load the experiment data
        fs::file exp_file = colortilt::experiment::find_file(name, baseloc);
        if (exp_file.path().empty()) {
            std::cerr << "Could not find experiment file!" << std::endl;
            return -1;
        }

        fs::file exp_yaml = fs::file(exp_file);

        if (!exp_file.exists()) {
            std::cerr << "Could no find experiment file" << std::endl;
            return -1;
        }

        colortilt::experiment exp = colortilt::experiment::from_yaml(exp_yaml);

        std::cout << "Color Tilt Experiment" << std::endl;
        std::cout << "Contrast BG: " << exp.c_bg << std::endl;
        std::cout << "Contrast FG: " << exp.c_fg << std::endl;
        std::cout << "Mouse gain:  " << exp.cursor_gain << std::endl;

        std::vector<std::string> sids = exp.subjects();


        std::vector<iris::data::subject> subjects;
        std::cout << std::endl << "Enrolled subjects: " << std::endl;
        for (const std::string &sid : sids) {
            std::cout << "  " << sid;
            iris::data::subject s;
            try {
                s = store.load_subject(sid);
                subjects.push_back(std::move(s));
            } catch (const std::exception &e) {
                std::cout << "\t[! unregisted subject]";
            }

            std::cout << std::endl;
        }

        std::cout << std::endl << "Subjects: " << std::endl;

        for (const iris::data::subject &subject : subjects) {
            std::vector<colortilt::session> sessions = exp.load_sessions(subject);
            session_set unique;

            std::cout << "  " << subject.name << std::endl;
            for (const colortilt::session &s : sessions) {
                unique.add(s);

            }

            std::vector<colortilt::trail> trails = exp.list_trails(subject);
            for (const colortilt::trail &trail : trails) {
                unique.add(trail);
            }

            int todo = 0;
            int done = 0;
            long diff = 0;
            for (const session_info &i : unique.sessions) {
                std::cout << "      " << i.name << "\t" << i.done.size();
                std::cout << " / " << i.todo.size() << std::endl;

                todo += i.todo.size();
                done += i.done.size();
                long d = i.todo.size() - i.done.size();

                if (d > 0) {
                    diff += d;
                }
            }

            std::cout << "    * Summary: \t " << done << " / " << todo;
            std::cout << " [" << diff << "]" << std::endl;
        }

    } catch (const std::exception &e) {
        std::cerr << e.what() << std::endl;
        return -1;
    }

    return 0;
}