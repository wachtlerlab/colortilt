
#include "exp.h"

#include <stdexcept>

int main(int argc, char **argv) {

    try {
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

        


    } catch (const std::exception &e) {
        std::cerr << e.what() << std::endl;
        return -1;
    }

    return 0;
}