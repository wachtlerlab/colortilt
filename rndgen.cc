#include <iris.h>
#include <misc.h>

#include <iostream>


#include <boost/program_options.hpp>
#include <boost/algorithm/string.hpp>

#include <random>
#include <numeric>
#include <algorithm>
#include <fs.h>
#include <stdlib.h>


bool do_debug = false;

int main(int argc, char **argv) {
    namespace po = boost::program_options;
    typedef std::mt19937 rnd_engine;

    size_t N = 0;
    size_t B = 1;
    rnd_engine::result_type seed = 0;
    std::string outfile = "";

    po::options_description opts("colortilt - random number generator");
    opts.add_options()
            ("help", "produce help message")
            ("file,F", po::value<std::string>(&outfile))
            ("blocks,B", po::value<size_t>(&B))
            ("number,N", po::value<size_t>(&N)->required())
            ("seed", po::value<rnd_engine::result_type>(&seed))
            ("debug", po::value<bool>(&do_debug));

    po::positional_options_description pos;
    pos.add("number", 1);

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

    std::vector<size_t> numbers(N);
    std::iota(numbers.begin(), numbers.end(), 0);

    std::random_device rnd_dev;
    rnd_engine rnd_gen(rnd_dev());

    if (seed == 0) {
        seed = rnd_gen();
    }

    rnd_gen.seed(seed);

    if (do_debug) {
        std::cerr << "#mt-seed: " << seed << std::endl;
        std::cerr << "#mt-state:  " << rnd_gen << std::endl;
    }

    // here comes the randomness
    // we assume that the stimuli come in B blocks, and that we
    // don't want to have two consecutive numbers from the *same*
    // block;

    auto dt = lldiv((long long int) N, (long long int) B);
    if (dt.rem != 0) {
        std::cerr << "N not evenly divisable by B." << dt.rem << "Meh!" << std::endl;
        return -1;
    }

    size_t blocksize = static_cast<size_t>(dt.quot);
    iris::block_shuffle(numbers.begin(), numbers.end(), blocksize, rnd_gen);

    if (B > 1) {
        // uniformly distributed # between [0, B)
        std::uniform_int_distribution<size_t> dis(0, B - 1);
        std::vector<size_t> urns(B, 0);
        std::vector<size_t> res;

        size_t last_urn = B;
        while (res.size() < N) {
            size_t cur_urn = dis(rnd_gen);

            if (cur_urn == last_urn) {
                if (do_debug) {
                    std::cerr << "[D] urn rep: " << cur_urn << " == " << last_urn << std::endl;
                }
                // check if we have any more numbers left in any other urn
                bool alternatives = false;
                for (size_t i = 0; !alternatives && i < B; i++) {
                    if (i == cur_urn) {
                        continue;
                    }

                    alternatives = urns[i] < blocksize;
                }

                if (alternatives) {
                    std::cerr << "[D] alternative present!" << std::endl;
                    continue;
                }
            }

            size_t idx = urns[cur_urn];

            std::cerr << "[D] " << cur_urn << std::endl;

            if (idx < blocksize) {
                size_t ni = idx + blocksize * cur_urn;
                const size_t num = numbers[ni];
                res.push_back(num);
                urns[cur_urn]++;
                last_urn = cur_urn;
                std::cerr << "[D] * " << num << std::endl;
            }

        }

        numbers = std::move(res);
    }


    std::stringstream outstr;
    outstr << "rnd";

    for (const size_t n : numbers) {
        outstr << std::endl << n;
    }

    if (outfile.empty()) {
        std::cout << outstr.str() << std::endl;
    } else {
        fs::file outfd(outfile);
        outfd.write_all(outstr.str());
    }

}