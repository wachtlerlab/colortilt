

#include <iris.h>

#include <glue/basic.h>
#include <glue/window.h>
#include <glue/shader.h>
#include <glue/buffer.h>
#include <glue/arrays.h>

#include <glm/gtc/matrix_transform.hpp>

#include <dkl.h>
#include <misc.h>

#include <cstdlib>
#include <numeric>
#include <random>
#include <iostream>

#include <boost/program_options.hpp>
#include <yaml-cpp/yaml.h>
#include <glue/text.h>
#include <scene.h>

#include "stimulus.h"
#include "scene.h"

namespace colortilt {

struct response {

    response(const colortilt::stimulus &s, double phi, double duration)
            : stimulus(s), phi(phi), duration(duration) { }

    colortilt::stimulus stimulus;

    double phi;
    double duration;
};

struct session {
    std::string stim;
    std::string rnd;

    static session from_string(const std::string &str);

    explicit operator bool() const {
        return !stim.empty() && !rnd.empty();
    }
};


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

struct experiment {
    double c_fg;
    double c_bg;

    std::string data_path;
    std::string stim_path;

    static experiment from_yaml(const fs::file &path);

    fs::file stim_file(const session &s) const;
    fs::file rnd_file(const session &s) const;

    fs::file resp_file(const session &ses, const iris::data::subject &sub) const;

    std::vector<session> load_sessions(const iris::data::subject &sub) const;
};


experiment experiment::from_yaml(const fs::file &path) {
    std::string data = path.read_all();
    YAML::Node doc = YAML::Load(data);
    YAML::Node root = doc["colortilt"];

    colortilt::experiment exp;
    exp.c_fg = root["contrast"]["fg"].as<double>();
    exp.c_bg = root["contrast"]["bg"].as<double>();
    exp.data_path = root["data-path"].as<std::string>();
    exp.stim_path = root["stim-path"].as<std::string>();

    return exp;
}


fs::file experiment::stim_file(const session &s) const {
    fs::file base = fs::file(stim_path);
    return base.child(s.stim + ".stm");
}

fs::file experiment::rnd_file(const session &s) const {
    fs::file base = fs::file(stim_path);
    return base.child(s.rnd + ".rnd");
}

fs::file experiment::resp_file(const session &ses, const iris::data::subject &sub) const {
    fs::file base = fs::file(data_path);
    fs::file sub_base = base.child(sub.identifier());
    fs::file resp_file = sub_base.child(ses.stim + "@" + ses.rnd + ".dat");
    return resp_file;
}


std::vector<session> experiment::load_sessions(const iris::data::subject &sub) const {
    fs::file base = fs::file(stim_path);
    fs::file session_file = base.child(sub.identifier() + ".sessions");

    if (! session_file.exists()) {
        std::cerr << "[W] EEXIST: " << session_file.path() << std::endl;
        return std::vector<session>();
    }

    std::string data = session_file.read_all();

    YAML::Node doc = YAML::Load(data);
    YAML::Node root = doc["sessions"];

    std::vector<session> sessions;
    std::transform(root.begin(), root.end(), std::back_inserter(sessions),
                   [](const YAML::Node &cn) {
                       return session::from_string(cn.as<std::string>());
                   });

    return sessions;
}
}

static glue::tf_font get_default_font() {
    iris::data::store store = iris::data::store::default_store();
    fs::file base = store.location();
    fs::file default_font = base.child("default.font").readlink();
    std::cerr << default_font.path() << " " << default_font.exists() << std::endl;

    if (default_font.exists()) {
        return glue::tf_font::make(default_font.path());
    } else {
        return glue::tf_font{};
    }
}


namespace gl = glue;
namespace ct = colortilt;

class ct_wnd : public gl::window {
public:
    ct_wnd(const iris::data::display &display,
           const ct::experiment &exp,
           iris::dkl &cspace,
           const std::vector<ct::stimulus> &stimuli,
           const std::vector<size_t> &rndseq,
           gl::extent phy_size)
            : window(display, "Color Tilt Experiment"), colorspace(cspace),
              stimuli(stimuli), rndseq(rndseq),
              c_fg(exp.c_fg), c_bg(exp.c_bg), board(cspace, c_fg), phy(phy_size) {
        make_current_context();
        glfwSwapInterval(1);

        box.init();
        board.init();

        stim_index = 0;

        cur_stim.phi_fg = 1.0f;
        cur_stim.phi_bg = 1.5f;

        gr_color = colorspace.reference_gray();
        intermission = false;

        disable_cursor();


    }

    const std::vector<ct::response>& responses() const {
        return resp;
    }

    virtual void framebuffer_size_changed(glue::extent size) override;
    virtual void pointer_moved(glue::point pos) override;
    virtual void key_event(int key, int scancode, int action, int mods) override;

    void render();

    void render_stimulus();
    void render_checkerboard();

    bool next_stimulus() {

        size_t cur_idx = stim_index++;

        if (cur_idx >= stimuli.size()) {
            return false;
        }

        //todo: handle rndseq.empty?
        size_t idx = rndseq[cur_idx];
        ct::stimulus cs = stimuli[idx];
        cur_stim = cs;

        if (cs.phi_bg < 0) {
            bg_color = colorspace.reference_gray();
        } else {
            bg_color = colorspace.iso_lum(cs.phi_bg, c_bg);
        }

        fg_color = colorspace.iso_lum(cs.phi_fg, c_fg);

        double offset = (rand() % 2 == 0 ? 1.0f : -1.0f) * (M_PI/2.0 + 0.05 * phi);
        change_phi(cs.phi_fg + offset, 1.0);

        return true;
    }

    void change_phi(double x, double gain) {
        phi += x * gain;
        phi = fmod(phi + (2.0f * M_PI), (2.0f * M_PI));
        cu_color = colorspace.iso_lum(phi, c_fg);
    }

    //member data

    iris::rgb fg_color = iris::rgb::gray();
    iris::rgb bg_color = iris::rgb::gray();
    iris::rgb cu_color = iris::rgb::gray();
    iris::rgb gr_color;

    iris::dkl &colorspace;
    const std::vector<ct::stimulus> &stimuli;
    const std::vector<size_t> &rndseq;
    size_t stim_index = 0;

    gl::point cursor;
    float cursor_gain = 0.0001;
    double phi = 0.0;
    double c_fg = 0.0;
    double c_bg = 0.0;

    ct::stimulus cur_stim;

    iris::rectangle box;
    iris::checkerboard board;

    gl::extent phy;
    bool intermission;

    std::vector<ct::response> resp;
    double stim_tstart;
};

void ct_wnd::pointer_moved(gl::point pos) {
    gl::window::pointer_moved(pos);

    float x = cursor.x - pos.x;
    change_phi(x, cursor_gain);
    cursor = pos;
}

void ct_wnd::framebuffer_size_changed(gl::extent size) {
    gl::window::framebuffer_size_changed(size);
}

void ct_wnd::key_event(int key, int scancode, int action, int mods) {
    window::key_event(key, scancode, action, mods);

    if (intermission) {
        return;
    }


    if (action != GLFW_PRESS) {
        return;
    }

    double gain = 2.25f;

    if (mods == GLFW_MOD_SHIFT) {
        gain *= 22.5f;
    } else if (mods == GLFW_MOD_CONTROL) {
        gain *= 1.0f;
    } else if (mods == GLFW_MOD_ALT) {
        gain *= .05f;
    }

    if (key == GLFW_KEY_SPACE) {

        if (stim_index != 0) {
            double now = glfwGetTime();
            double dur = now - stim_tstart;
            std::cerr << cur_stim.size << ", ";
            std::cerr << cur_stim.phi_bg << ", ";
            std::cerr << cur_stim.phi_fg << ", ";
            std::cerr << phi << ", ";
            std::cerr << cur_stim.side << ", ";
            std::cerr << dur << std::endl;

            resp.emplace_back(cur_stim, phi, dur);
        }

        bool keep_going = next_stimulus();
        should_close(!keep_going);
        intermission = true;
        board.reset_timer();
    } else if (key == GLFW_KEY_RIGHT) {
        change_phi(M_PI / 180.0, gain);
    } else if (key == GLFW_KEY_LEFT) {
        change_phi(-1.0 * M_PI / 180.0, gain);
    } else if (key == GLFW_KEY_I) {
        std::cerr << phi << " " << cu_color;
    } else if (key == GLFW_KEY_R) {
        cursor_gain = 0.0001;
    } else if (key == GLFW_KEY_S) {
        cursor_gain *= 0.5;
    } else if (key == GLFW_KEY_D) {
        cursor_gain *= 2.0;
    }
}


void ct_wnd::render() {
    if (intermission) {
        render_checkerboard();

        double cb_time = board.duration();
        if (cb_time > 2.0f) {
            intermission = false;
            stim_tstart = glfwGetTime();
        }

    } else {
        render_stimulus();
    }
}

void ct_wnd::render_checkerboard() {
    const float stim_size = cur_stim.size;

    board.configure(phy, gl::extent(stim_size, stim_size));
    glm::mat4 projection = glm::ortho(0.f, phy.width, phy.height, 0.f);
    board.draw(projection);

}

void ct_wnd::render_stimulus() {

    gl::extent fb = framebuffer_size();
    glm::mat4 px2gl = glm::ortho(0.0f, fb.width, fb.height, 0.0f);
    glm::mat4 gl2px = glm::inverse(px2gl);

    glm::mat4 tpp = glm::translate(glm::mat4(1), glm::vec3(0.375f, 0.375f, 0.0f));

    glm::mat4 ppp = px2gl * tpp * gl2px;

    glm::mat4 projection = ppp * glm::ortho(0.f, phy.width, phy.height, 0.f);
    glm::mat4 ttrans = glm::translate(glm::mat4(1), glm::vec3(phy.width*.5f, 0.f, 0.0f));

    const float stim_size = cur_stim.size;

    const float center_x = phy.width * .25f - (stim_size * .5f);
    const float center_y = phy.height * .5f - (stim_size * .5f);

    glm::mat4 tr_center = glm::translate(glm::mat4(1), glm::vec3(center_x, center_y, 0.0f));

    glm::mat4 vp_stim = projection * ttrans;
    glm::mat4 vp_bg = projection;

    if (cur_stim.side == 'l') {
        using std::swap;
        swap(vp_bg, vp_stim);
    }

    glClearColor(gr_color.r, gr_color.b, gr_color.b, 1.0f);
    glClear(GL_COLOR_BUFFER_BIT);

    // background with color
    box.configure(gl::extent(phy.width * .5f, phy.height));
    box.configure(bg_color);
    box.draw(vp_stim);

    // foreground with color
    box.configure(gl::extent(stim_size, stim_size));
    box.configure(fg_color);
    box.draw(vp_stim * tr_center);

    // user choice on gray background
    box.configure(gl::extent(stim_size, stim_size));
    box.configure(cu_color);
    box.draw(vp_bg * tr_center);
}

static fs::file find_experiment_file() {

    static std::vector<fs::file> known_files = {
            fs::file("colortilt.experiment"),
            fs::file("~/colortilt.experiment"),
            fs::file("~/experiment/colortilt.experiment"),
            fs::file("~/experiment/colortilt/experiment")
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


int main(int argc, char **argv) {
    namespace po = boost::program_options;

    float gray_level = -1;
    std::string sid = "";

    po::options_description opts("colortilt experiment");
    opts.add_options()
            ("help", "produce help message")
            ("gray", po::value<float>(&gray_level), "reference gray [default=read from rgb2lms]")
            ("subject,S", po::value<std::string>(&sid)->required());

    po::positional_options_description pos;
    pos.add("subject", 1);

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

    // load the experiment data
    fs::file exp_file = find_experiment_file();
    if (exp_file.path().empty()) {
        std::cerr << "Could not find experiment file!" << std::endl;
        return -1;
    }
    fs::file exp_yaml = fs::file(exp_file);
    ct::experiment exp = ct::experiment::from_yaml(exp_yaml);

    std::cerr << "[I] data path: " << exp.data_path << std::endl;
    std::cerr << "[I] stim path: " << exp.stim_path << std::endl;

    // the display env
    iris::data::store store = iris::data::store::default_store();
    std::string mdev = store.default_monitor();

    iris::data::monitor moni = store.load_monitor(mdev);
    iris::data::monitor::mode mode = moni.default_mode;
    iris::data::display display = store.make_display(moni, mode, "gl");
    iris::data::rgb2lms rgb2lms = store.load_rgb2lms(display);

    iris::dkl::parameter params = rgb2lms.dkl_params;
    gl::extent phy_size(rgb2lms.width, rgb2lms.height);

    if (gray_level < 0) {
        gray_level = rgb2lms.gray_level;
    } else {
        std::cerr << "[W] overriding gray-level: ";
        std::cerr << gray_level << "* " << rgb2lms.gray_level;
        std::cerr << std::endl;
    }


    std::cerr << "[I] contrast fg: " << exp.c_fg << std::endl;
    std::cerr << "[I] contrast bg: " << exp.c_bg << std::endl;
    std::cerr << "[I] gray-level: " << gray_level << std::endl;

    std::cerr << "[I] rgb2sml calibration:" << std::endl;
    params.print(std::cerr);
    iris::rgb refpoint(iris::rgb::gray(gray_level));
    iris::dkl cspace(params, refpoint);

    std::vector<iris::data::subject> hits = store.find_subjects(sid);
    if (hits.empty()) {
        std::cerr << "Coud not find subject [" << sid << "]" << std::endl;
    } else if (hits.size() > 1) {
        std::cerr << "Ambigous subject string (> 1 hits): " << std::endl;
        for (const auto &s : hits) {
            std::cerr << "\t" << s.initials << std::endl;
        }
    }

    const iris::data::subject subject = hits.front(); // size() == 1 asserted
    iris::data::isoslant iso = store.load_isoslant(subject);
    cspace.iso_slant(iso.dl, iso.phi);

    std::cerr << "[I] subject: " << subject.identifier() << std::endl;
    std::cerr << "[I] isoslant: [dl: " << iso.dl << ", " << iso.phi << "]" << std::endl;


    // load the stimulus
    std::vector<ct::session> sessions = exp.load_sessions(subject);
    if (sessions.empty()) {
        std::cerr << "[E] no sessions found!" << std::endl;
        return -10;
    } else {
        std::cerr << "[I] " << sessions.size() << " sessions found." << std::endl;
    }

    std::cerr << "[I] checking sessions" << std::endl;
    ct::session session;
    for (const ct::session &ses : sessions) {
        fs::file rsf = exp.resp_file(ses, subject);
        std::cerr << "\t [" << rsf.name() << "] ";
        bool have_resp = rsf.exists();
        std::cerr << (have_resp ? u8"✓" : u8"︎") << std::endl;

        if (!have_resp) {
            session = ses;
            break;
        }
    }

    if (!session) {
        std::cerr << "[E] No available session to do!" << std::endl;
        return 0;
    }

    fs::file stim_file = exp.stim_file(session);
    std::cerr << "[I] stim file: " << stim_file.path() << std::endl;

    fs::file rnd_file = exp.rnd_file(session);
    std::cerr << "[I] rnd# file: " << rnd_file.path() << std::endl;

    std::vector<ct::stimulus> stimuli = ct::stimulus::from_csv(stim_file.path());
    std::vector<size_t> rndseq = ct::load_rnd_data(rnd_file);

    std::cerr << "[I] Stimuli N: " << stimuli.size() << std::endl;
    std::cerr << "[I] Random# N: " << rndseq.size() << std::endl;

    if (stimuli.empty() || rndseq.empty()) {
        std::cerr << "[E] No stimuli to present!!" << std::endl;
        return -2;
    }

    if (!glfwInit()) {
        return -1;
    }

    std::srand(31337); // so random, very wow!

    ct_wnd wnd(display, exp, cspace, stimuli, rndseq, phy_size);

    while (! wnd.should_close()) {
        wnd.render();

        wnd.swap_buffers();
        glfwPollEvents();
    }

    //
    std::stringstream outstr;
    outstr << "size, bg, fg, phi, side, duration";
    for (const auto &resp : wnd.responses()) {
        outstr << std::endl;
        outstr << resp.stimulus.size << ", ";
        outstr << resp.stimulus.phi_bg << ", ";
        outstr << resp.stimulus.phi_fg << ", ";
        outstr << resp.phi << ", ";
        outstr << resp.stimulus.side << ", ";
        outstr << static_cast<float>(resp.duration);
    }

    std::cerr << outstr.str() << std::endl;

    if (rndseq.size() == wnd.responses().size()) {
        fs::file rsf = exp.resp_file(session, subject);
        fs::file data_dir = rsf.parent();
        data_dir.mkdir_with_parents();
        rsf.write_all(outstr.str());

        std::cout << "Worte data to: " << rsf.path() << std::endl;
    }

    glfwTerminate();
    return 0;
}