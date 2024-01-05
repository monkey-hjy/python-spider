t = {}
t["_encrypt"] = function() {
    return (t["_encrypt"] = t["asm"]["encrypt"]).apply(null, arguments)
}
t["stackSave"] = function() {
    return (bt = t["stackSave"] = t["asm"]["stackSave"]).apply(null, arguments)
}

function ot(n) {
    t["onAbort"] && t["onAbort"](n),
    n += "",
    S(n),
    j = !0,
    1,
    n = "abort(" + n + "). Build with -s ASSERTIONS=1 for more info.";
    var e = new WebAssembly.RuntimeError(n);
    throw c(e),
    e
}

function k(t, n) {
    t || ot("Assertion failed: " + n)
}

function I(n) {
    var e = t["_" + n];
    return k(e, "Cannot call unknown function " + n + ", make sure it is exported"),
    e
}

function L(t, n, e, r, i) {
    var o = {
        string: function(t) {
            var n = 0;
            if (null !== t && void 0 !== t && 0 !== t) {
                var e = 1 + (t.length << 2);
                n = xt(e),
                N(t, n, e)
            }
            return n
        },
        array: function(t) {
            var n = xt(t.length);
            return D(t, n),
            n
        }
    };
    function a(t) {
        return "string" === n ? W(t) : "boolean" === n ? Boolean(t) : t
    }
    var c = I(t)
      , u = []
      , s = 0;
    if (r)
        for (var f = 0; f < r.length; f++) {
            var l = o[e[f]];
            console.log('l: ', l)
            l ? (0 === s && (s = bt()),
            u[f] = l(r[f])) : u[f] = r[f]
        }
    var h = c.apply(null, u);
    return h = a(h),
    0 !== s && _t(s),
    h
}
L("encrypt", "string", ["string", "string"], ['/api/movie', 1655534908]);