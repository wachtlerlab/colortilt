
#include "exp.h"

#include <stdexcept>

int main(int argc, char **argv) {

    try {
        iris::data::store store = iris::data::store::default_store();

        // load the experiment data
        fs::file exp_file = colortilt::experiment::find_file("");
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

        std::cout << std::endl << "Sessions: " << std::endl;
        for (const iris::data::subject &subject : subjects) {
            std::vector<colortilt::session> sessions = exp.load_sessions(subject);

            std::cout << "  " << subject.name << std::endl;
            for (const colortilt::session &s : sessions) {
                std::cout << "    " << s.name() << std::endl;
            }

        }


    } catch (const std::exception &e) {
        std::cerr << e.what() << std::endl;
        return -1;
    }

    return 0;
}