

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
    double cursor_gain;

    std::string data_path;
    std::string stim_path;
    std::string sess_path;

    static experiment from_yaml(const fs::file &path);

    fs::file session_file(const iris::data::subject &s) const;
    fs::file stim_file(const session &s) const;
    fs::file rnd_file(const session &s) const;

    fs::file resp_file(const session &ses, const iris::data::subject &sub, const std::string &prefix = "") const;

    std::vector<session> load_sessions(const iris::data::subject &sub) const;
    session next_session(const iris::data::subject &sub) const;
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
    exp.sess_path = root["sess-path"].as<std::string>();
    exp.cursor_gain = root["cursor-gain"].as<double>();

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


fs::file experiment::session_file(const iris::data::subject  &s) const {
    fs::file base = fs::file(sess_path);
    fs::file session_file = base.child(s.identifier() + ".sessions");
    return session_file;
}

fs::file experiment::resp_file(const session &ses, const iris::data::subject &sub, const std::string &prefix) const {
    fs::file base = fs::file(data_path);
    fs::file sub_base = base.child(sub.identifier());
    fs::file resp_file = sub_base.child(prefix + ses.name() + ".dat");
    return resp_file;
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


session experiment::next_session(const iris::data::subject &sub) const {
    std::string timebase = iris::make_timestamp();
    const size_t ts_size = timebase.size();

    fs::file base = fs::file(data_path);
    fs::file data_dir = base.child(sub.identifier());

    std::vector<fs::file> dat_files;
    std::copy_if(data_dir.children().begin(), data_dir.children().end(),
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

    std::cerr << "[I] checking sessions" << std::endl;

    for (std::string name : dat_names) {
        std::cerr << "\t Found " << name << std::endl;
    }

    std::vector<session> sessions = load_sessions(sub);
    for (const session &se : sessions) {
        fs::file rsf = resp_file(se, sub);
        std::string rsf_name = se.name();
        auto n_stim = std::count_if(sessions.cbegin(), sessions.cend(),
                                    [&rsf_name](const session &cur_session) {
                                        return rsf_name == cur_session.name();
                                    });

        auto n_resp = std::count_if(dat_names.begin(), dat_names.end(),
                                    [&rsf_name](const std::string &cur_name) {
                                        return rsf_name == cur_name;
                                    });

        std::cerr << "\t [" << rsf.name() << "] # " << n_resp << "/" << n_stim;
        bool needs_doing = n_resp < n_stim;
        std::cerr << (needs_doing ? u8" *" : u8" ✓") << std::endl;

        if (needs_doing) {
            return se;
        }
    }

    return colortilt::session();
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
              c_fg(exp.c_fg), c_bg(exp.c_bg),
              cursor_gain(exp.cursor_gain), board(cspace, c_fg), phy(phy_size),
              rd(), rd_gen(rd()) {
        make_current_context();
        glfwSwapInterval(1);
        disable_cursor();

        box.init();
        board.init();

        stim_index = 0;

        cur_stim.phi_fg = 1.0f;
        cur_stim.phi_bg = 1.5f;
        cur_stim.size = 20;
        cur_stim.side = 'r';

        gr_color = colorspace.reference_gray();
        intermission = false;

        progress = iris::scene::label(get_default_font(), "colortilt", 16);
        progress.init();

        fg_color = iris::rgb::gray();
        bg_color = iris::rgb::gray();
        cu_color = iris::rgb::gray();

        change_phi(0, 0);
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
            bg_color = colorspace.iso_lum(cs.phi_bg, c_bg, true);
        }

        fg_color = colorspace.iso_lum(cs.phi_fg, c_fg, true);

        std::uniform_real_distribution<double> dst(-45.0, 45.0);
        double offset = dst(rd_gen);

        phi = 0; // change_phi adds to current phi, so reset it
        phi_start = fmod(cs.phi_fg + offset + 360.0, 360.0);

        change_phi(phi_start, 1.0);

        //update the progress
        std::stringstream sstr;
        sstr << cur_idx << " of " << stimuli.size();
        progress.text(sstr.str());

        return true;
    }

    void change_phi(double x, double gain) {
        phi += x * gain;
        phi = fmod(phi + 360.0, 360.0);
        cu_color = colorspace.iso_lum(phi, c_fg, true);
    }

    //member data

    iris::rgb fg_color;
    iris::rgb bg_color;
    iris::rgb cu_color;
    iris::rgb gr_color;

    iris::dkl &colorspace;
    const std::vector<ct::stimulus> &stimuli;
    const std::vector<size_t> &rndseq;
    size_t stim_index = 0;

    double phi = 0.0;
    double phi_start = 0.0;
    double c_fg = 0.0;
    double c_bg = 0.0;

    float cursor_gain = 0.001;
    gl::point cursor;

    ct::stimulus cur_stim;

    iris::rectangle box;
    iris::checkerboard board;

    gl::extent phy;
    bool intermission;

    std::vector<ct::response> resp;
    double stim_tstart;

    iris::scene::label progress;

    std::random_device rd;
    std::mt19937 rd_gen;
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
            std::cerr << phi_start << ", ";
            std::cerr << phi << ", ";
            std::cerr << cur_stim.side << ", ";
            std::cerr << dur << std::endl;

            resp.emplace_back(cur_stim, phi, dur, phi_start);
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

    if (cur_stim.side == 'r') {
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

    // the progress
    progress.draw(px2gl);
}

static fs::file find_experiment_file() {

    static std::vector<fs::file> known_files = {
            fs::file("colortilt.experiment"),
            fs::file("~/colortilt.experiment"),
            fs::file("~/experiments/colortilt.experiment"),
            fs::file("~/experiments/colortilt/experiment")
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

    std::string exp_start = iris::make_timestamp();

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
    std::cerr << "[I] sess path: " << exp.sess_path << std::endl;

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
    std::cerr << "[I] cursor-gain: " << exp.cursor_gain << std::endl;

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

    ct::session session = exp.next_session(subject);

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

    glEnable(GL_BLEND);
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
    glEnable(GL_VERTEX_PROGRAM_POINT_SIZE);

    while (! wnd.should_close()) {
        wnd.render();

        wnd.swap_buffers();
        glfwPollEvents();
    }

    //
    std::stringstream outstr;
    outstr << "size, bg, fg, phi_start, phi, side, duration";
    for (const auto &resp : wnd.responses()) {
        outstr << std::endl;
        outstr << resp.stimulus.size << ", ";
        outstr << resp.stimulus.phi_bg << ", ";
        outstr << resp.stimulus.phi_fg << ", ";
        outstr << resp.phi_start << ", ";
        outstr << resp.phi << ", ";
        outstr << resp.stimulus.side << ", ";
        outstr << static_cast<float>(resp.duration);
    }

    std::cerr << outstr.str() << std::endl;

    bool is_complete = rndseq.size() == wnd.responses().size();
    
    fs::file rsf = exp.resp_file(session, subject, exp_start + "_");

    if (! is_complete) {
        rsf = fs::file(rsf.path() + ".x");
    }

    fs::file data_dir = rsf.parent();
    data_dir.mkdir_with_parents();
    rsf.write_all(outstr.str());
    std::cout << "Worte data to: " << rsf.path() << std::endl;

    glfwTerminate();
    return 0;
}