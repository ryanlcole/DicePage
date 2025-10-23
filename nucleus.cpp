#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <map>
#include <string>

namespace py = pybind11;

/*
    Shaelvien Nucleus v2 — Glyph Registry + Power I/O
    -------------------------------------------------
    Each glyph has: id, color, type, active flag, resonance.
    Provides: set_power / get_power / activate / deactivate / map / ask
*/

struct Glyph {
    std::string id;
    std::string type;
    std::string color;
    bool        active = false;
    double      resonance = 1.0;
};

class Nucleus {
private:
    std::string power_state = "active";
    std::map<std::string, Glyph> registry;

public:
    Nucleus() {
        // bootstrap glyphs
        registry = {
            {"daemon", {"daemon","system","#9b59b6",false,0.85}},
            {"tray",   {"tray","system","#3498db",false,0.95}},
            {"hud",    {"hud","system","#2ecc71",false,1.10}},
            {"spark",  {"spark","system","#f1c40f",false,1.60}},
            {"solar",  {"solar","system","#e67e22",false,1.25}},
            {"lunar",  {"lunar","system","#95a5a6",false,0.60}},
            {"stone",  {"stone","system","#7f8c8d",false,0.50}},
            {"element",{"element","placeholder","#1abc9c",false,1.40}},
            {"matter", {"matter","placeholder","#16a085",false,0.70}},
            {"dna",    {"dna","placeholder","#e84393",false,1.15}},
            {"wave",   {"wave","placeholder","#2980b9",false,1.80}}
        };
    }

    // --- Power Control ---
    void set_power(const std::string &state) {
        if (state=="off"||state=="standby"||state=="active")
            power_state = state;
    }
    std::string get_power() const { return power_state; }

    // --- Glyph Operations ---
    void activate(const std::string &gid) {
        if (registry.count(gid)) registry[gid].active = true;
    }
    void deactivate(const std::string &gid) {
        if (registry.count(gid)) registry[gid].active = false;
    }

    std::map<std::string,Glyph> get_map() const { return registry; }

    std::string ask(const std::string &q) const {
        return "[nucleus] You asked: " + q +
               " | Power:" + power_state +
               " | Glyphs:" + std::to_string(registry.size());
    }
};

// --- PyBind glue ---
PYBIND11_MODULE(shaelvien_nucleus, m) {
    py::class_<Glyph>(m,"Glyph")
        .def_readwrite("id",&Glyph::id)
        .def_readwrite("type",&Glyph::type)
        .def_readwrite("color",&Glyph::color)
        .def_readwrite("active",&Glyph::active)
        .def_readwrite("resonance",&Glyph::resonance);

    py::class_<Nucleus>(m,"Nucleus")
        .def(py::init<>())
        .def("set_power",&Nucleus::set_power)
        .def("get_power",&Nucleus::get_power)
        .def("activate",&Nucleus::activate)
        .def("deactivate",&Nucleus::deactivate)
        .def("get_map",&Nucleus::get_map)
        .def("ask",&Nucleus::ask);
}
