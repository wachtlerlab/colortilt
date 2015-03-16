//
// Created by Christian Kellner on 13/03/15.
//

#include <iris.h>
#include <misc.h>

#include <iostream>


#include <boost/program_options.hpp>

#include <random>
#include <numeric>
#include <algorithm>

#include "stimulus.h"

namespace ct = colortilt;

int main(int argc, char **argv) {

    namespace po = boost::program_options;

    std::string ca_path;
    size_t nfg = 16;
    size_t nbg = 8;
    size_t nblocks = 2;
    std::vector<float> sizes = {40, 60};
    float angles = -1.0f;

    po::options_description opts("calibration tool");
    opts.add_options()
            ("help", "produce help message")
            ("backgrounds,b", po::value<size_t>(&nbg))
            ("foregrounds,f", po::value<size_t>(&nfg))
            ("blocks,N", po::value<size_t>(&nblocks))
            ("angles,a", po::value<float>(&angles))
            ("sizes,s", po::value<std::vector<float>>(&sizes));

    po::positional_options_description pos;

    po::variables_map vm;
    try {
        po::store(po::command_line_parser(argc, argv).options(opts).positional(pos).run(), vm);
        po::notify(vm);
    } catch (const std::exception &e) {
        std::cerr << "Error while parsing commad line options: " << std::endl;
        std::cerr << "\t" << e.what() << std::endl;
        return 1;
    }

    if (vm.count("help") > 0) {
        std::cout << opts << std::endl;
        return 0;
    }

    if (angles > -1.0f) {
        std::transform(sizes.begin(), sizes.end(), sizes.begin(), [angles](const float v){
            return iris::visual_angle_to_size(v, angles);
        });
    }

    std::vector<double> fgs = iris::linspace(0.0, 2*M_PI, nfg);
    std::vector<double> bgs = iris::linspace(0.0, 2*M_PI, nbg);

    size_t total = fgs.size() * bgs.size() * sizes.size();
    std::vector<ct::stimulus> stimuli;
    stimuli.reserve(total);

    for(size_t i = 0; i < fgs.size(); i++) {
        for(size_t j = 0; j < bgs.size(); j++) {
            for(size_t k = 0; k < sizes.size(); k++) {
                stimuli.emplace_back(fgs[i], bgs[j], sizes[k]);
            }
        }
    }

    std::random_device rnd_dev;
    std::mt19937 rnd_gen(rnd_dev());

    for (size_t i = 0; i < nblocks; i++) {

        std::shuffle(stimuli.begin(), stimuli.end(), rnd_gen);

        for (ct::stimulus s : stimuli) {
            std::cout.width(8);
            std::cout << s.phi_fg << ", ";
            std::cout.width(8);
            std::cout << s.phi_bg << ", ";
            std::cout.width(2);
            std::cout << s.size << std::endl;
        }

        std::cout << std::endl;
        std::cout << std::endl;
    }

    return 0;
}