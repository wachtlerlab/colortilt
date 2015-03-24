//
// Created by Christian Kellner on 13/03/15.
//

#include <iris.h>
#include <misc.h>

#include <iostream>


#include <boost/program_options.hpp>
#include <boost/algorithm/string.hpp>

#include <random>
#include <numeric>
#include <algorithm>

#include "stimulus.h"

namespace ct = colortilt;

//TODO: move to general iris
namespace iris {

template<typename T>
bool special_value(const std::string &str, T &val) {
    return false;
}

template<>
bool special_value<double>(const std::string &str, double &val) {
    if (str == "π") {
        val = M_PI;
        return true;
    } else if (str == "τ") {
        val = 2*M_PI;
        return true;
    }

    return false;
}

template<typename T>
struct slice_t {

    slice_t() : stop(T(0)), start(T(0)), step(T(0)) {
    }

    slice_t(T stop) : stop(stop), start(T(0)), step(T(1)) {
    }

    slice_t(T stop, T start) : stop(stop), start(start), step(T(1)) {
    }

    slice_t(T stop, T start, T step) : stop(stop), start(start), step(step) {
    }

    struct iterator {
        typedef T value_type;
        typedef ptrdiff_t difference_type;
        typedef const value_type *pointer;
        typedef const value_type &reference;
        typedef std::input_iterator_tag iterator_category;

        iterator() : s(), pos(T(0)) {
        }

        iterator(slice_t<T> s) : s(std::move(s)), pos(s.start) {
        }

        iterator &operator++() {
            pos += s.step;
            return *this;
        }

        iterator operator++(int) {
            iterator tmp(*this);
            ++(*this);
            return tmp;
        }

        reference operator*() const {
            return pos;
        }

        pointer operator->() const {
            return &pos;
        }

        bool operator==(const iterator &other) const {
            if (other.pos >= other.s.stop && this->pos >= this->s.stop) {
                return true;
            }

            return other.s == this->s && other.pos == this->pos;
        }

        bool operator!=(const iterator &other) const {
            return !(*this == other);
        }

    private:
        slice_t<T> s;
        T pos;
    };

    iterator begin() const {
        return iterator(*this);
    }

    iterator end() const {
        return iterator();
    }

    iterator cbegin() const {
        return iterator(*this);
    }

    iterator cend() const {
        return iterator();
    }

    bool operator==(const slice_t<T> &o) const {
        return stop == o.stop && start == o.stop && step == o.step;
    }

    bool operator!=(const slice_t<T> &o) const {
        return !(*this == o);
    }

    static slice_t from_string(const std::string str) {
        auto pos = std::find(std::begin(str), std::end(str), ':');
        if (pos == std::end(str)) {
            return slice_t();
        }

        std::vector<std::string> strs;
        std::vector<double> dbl;

        boost::split(strs, str, boost::is_any_of(":"));
        std::transform(strs.cbegin(), strs.cend(), std::back_inserter(dbl), [](const std::string &val) {
            T sv;
            if (special_value(val, sv)) {
                return sv;
            }
            return boost::lexical_cast<T>(val);
        });

        switch (dbl.size()) {
            case 3: return slice_t(dbl[2], dbl[0], dbl[1]);
            case 2: return slice_t(dbl[1], dbl[0]);
            case 1: return slice_t(dbl[0]);;
            case 0: //ft
            default: throw std::invalid_argument("Too many or zero values");

        }
    }

    T stop;
    T start;
    T step;
};

typedef slice_t<double> slice;


struct opt_range {

    opt_range() : vals() { }
    explicit opt_range(double v) : vals({v}) { }
    explicit opt_range(const std::vector<double> &v) : vals(v) { }

    std::vector<double> vals;
};

void validate(boost::any &v,
              const std::vector<std::string> &values,
              opt_range *target_type, int) {
    using namespace boost::program_options;

    validators::check_first_occurrence(v);
    const std::string &s = validators::get_single_string(values);


    auto pos = std::find(std::begin(s), std::end(s), ':');
    if (pos != std::end(s)) {
        slice sl = slice::from_string(s);
        std::vector<double> res;
        std::copy(sl.cbegin(), sl.cend(), std::back_inserter(res));
        v = boost::any(opt_range(res));
        return;
    }

    pos = std::find(std::begin(s), std::end(s), ',');
    if (pos != std::end(s)) {
        std::vector<std::string> strs;
        boost::split(strs, s, boost::is_any_of(","));

        std::vector<double> dbl;
        std::transform(strs.cbegin(), strs.cend(), std::back_inserter(dbl), [](const std::string &val) {
            return std::stod(val);
        });
        v = boost::any(opt_range(dbl));
        return;
    }

    double val = std::stod(s);
    v = boost::any(opt_range(val));
}

} //iris


int main(int argc, char **argv) {

    namespace po = boost::program_options;

    std::string ca_path;
    size_t nblocks = 2;
    std::vector<float> sizes = {20, 40, 60};
    float angles = -1.0f;
    bool in_degree = false;
    bool no_shuffle = false;
    iris::opt_range rbg(8);
    iris::opt_range rfg(16);


    po::options_description opts("calibration tool");
    opts.add_options()
            ("help", "produce help message")
            ("backgrounds,b", po::value<iris::opt_range>(&rbg))
            ("foregrounds,f", po::value<iris::opt_range>(&rfg))
            ("blocks,N", po::value<size_t>(&nblocks))
            ("angles,a", po::value<float>(&angles))
            ("degree", po::value<bool>(&in_degree))
            ("sizes,s", po::value<std::vector<float>>(&sizes))
            ("no-shuffle", po::value<bool>(&no_shuffle));

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

    std::vector<double> fgs;
    std::vector<double> bgs;
    if (rfg.vals.size() == 1) {
        fgs = iris::linspace(0.0, 2 * M_PI,static_cast<size_t>(rfg.vals[0]));
        if (in_degree) {
            std::transform(fgs.cbegin(), fgs.cend(), fgs.begin(), [](double v){
                return v / M_PI * 180.0;
            });
        }
    } else {
        fgs = rfg.vals;
    }

    if (rbg.vals.size() == 1) {
        bgs = iris::linspace(0.0, 2 * M_PI, static_cast<size_t>(rbg.vals[0]));
        if (in_degree) {
            std::transform(bgs.cbegin(), bgs.cend(), bgs.begin(), [](double v){
                return v / M_PI * 180.0;
            });
        }
    } else {
        bgs = rbg.vals;
    }

    if (in_degree) {
        std::transform(bgs.cbegin(), bgs.cend(), bgs.begin(), [](double v){
            return v / 180.0 * M_PI;
        });

        std::transform(fgs.cbegin(), fgs.cend(), fgs.begin(), [](double v){
            return v / 180.0 * M_PI;
        });
    }

    size_t total = fgs.size() * bgs.size() * sizes.size();
    std::vector<ct::stimulus> stimuli;
    stimuli.reserve(total);

    for(size_t i = 0; i < fgs.size(); i++) {
        for(size_t j = 0; j < bgs.size(); j++) {
            for(size_t k = 0; k < sizes.size(); k++) {
                char side = (i+j+k) % 2 == 0 ? 'l' : 'r';
                stimuli.emplace_back(fgs[i], bgs[j], sizes[k], side);
            }
        }
    }

    std::random_device rnd_dev;
    std::mt19937 rnd_gen(rnd_dev());

    for (size_t i = 0; i < nblocks; i++) {

        if (!no_shuffle) {
            std::shuffle(stimuli.begin(), stimuli.end(), rnd_gen);
        }

        for (ct::stimulus s : stimuli) {
            std::cout.width(8);
            std::cout << s.phi_fg << ", ";
            std::cout.width(8);
            std::cout << s.phi_bg << ", ";
            std::cout.width(2);
            std::cout << s.size << ", ";
            std::cout.width(1);
            std::cout << s.side << std::endl;
        }

        std::cout << std::endl;
        std::cout << std::endl;
    }

    return 0;
}