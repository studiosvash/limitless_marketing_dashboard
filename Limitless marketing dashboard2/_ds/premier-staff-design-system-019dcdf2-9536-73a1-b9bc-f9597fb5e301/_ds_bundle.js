/* @ds-bundle: {"format":3,"namespace":"PremierStaffDesignSystem_019dcd","components":[],"sourceHashes":{"ui_kits/marketing-website/Bento.jsx":"f2e5107f7e93","ui_kits/marketing-website/BookingSteps.jsx":"3d3bfabbf8d2","ui_kits/marketing-website/Buttons.jsx":"f193b9cd2451","ui_kits/marketing-website/FAQ.jsx":"dca227a024eb","ui_kits/marketing-website/Footer.jsx":"b5480c45e031","ui_kits/marketing-website/Hero.jsx":"65e4690ebec8","ui_kits/marketing-website/HeroCentered.jsx":"df6269a31cb6","ui_kits/marketing-website/Nav.jsx":"96e479bf9be4","ui_kits/marketing-website/Rating.jsx":"407ec54bce5d","ui_kits/marketing-website/Review.jsx":"4b078fcf93b5","ui_kits/marketing-website/SectionTitle.jsx":"d21622341533","ui_kits/marketing-website/TrustedBy.jsx":"07fbdc9c43e6"},"inlinedExternals":[],"unexposedExports":[]} */

(() => {

const __ds_ns = (window.PremierStaffDesignSystem_019dcd = window.PremierStaffDesignSystem_019dcd || {});

const __ds_scope = {};

(__ds_ns.__errors = __ds_ns.__errors || []);

// ui_kits/marketing-website/Bento.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
// Premier Staff — Bento tile grid (image + flat dark variants)
const BentoTile = ({
  title,
  image,
  dark,
  span = 1,
  height = 240
}) => /*#__PURE__*/React.createElement("div", {
  style: {
    gridColumn: `span ${span}`,
    height,
    position: "relative",
    borderRadius: 12,
    overflow: "hidden",
    background: dark ? "rgb(55,55,55)" : "var(--ink-450)",
    boxShadow: "0 4px 4px rgba(0,0,0,0.05)",
    transition: "box-shadow 220ms var(--ease-standard), transform 220ms var(--ease-standard)",
    cursor: "pointer"
  },
  onMouseEnter: e => {
    e.currentTarget.style.transform = "translateY(-2px)";
    e.currentTarget.style.boxShadow = "0 8px 24px rgba(0,0,0,0.10)";
  },
  onMouseLeave: e => {
    e.currentTarget.style.transform = "translateY(0)";
    e.currentTarget.style.boxShadow = "0 4px 4px rgba(0,0,0,0.05)";
  }
}, image && /*#__PURE__*/React.createElement("img", {
  src: image,
  alt: "",
  style: {
    position: "absolute",
    inset: 0,
    width: "100%",
    height: "100%",
    objectFit: "cover"
  }
}), image && /*#__PURE__*/React.createElement("div", {
  style: {
    position: "absolute",
    inset: 0,
    background: "linear-gradient(180deg, rgba(0,0,0,0) 50%, rgba(0,0,0,0.55))"
  }
}), /*#__PURE__*/React.createElement("h4", {
  style: {
    position: "absolute",
    left: 24,
    bottom: 22,
    margin: 0,
    font: "400 30px/1.2 var(--font-body)",
    letterSpacing: "var(--track-snug)",
    color: dark ? "rgb(217,217,217)" : "#fff",
    maxWidth: "85%"
  }
}, title));
const Bento = ({
  tiles
}) => /*#__PURE__*/React.createElement("section", {
  style: {
    padding: "0 84px 84px"
  }
}, /*#__PURE__*/React.createElement("div", {
  style: {
    display: "grid",
    gridTemplateColumns: "repeat(4, 1fr)",
    gap: 16
  }
}, tiles.map((t, i) => /*#__PURE__*/React.createElement(BentoTile, _extends({
  key: i
}, t)))));
window.Bento = Bento;
window.BentoTile = BentoTile;
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/marketing-website/Bento.jsx", error: String((e && e.message) || e) }); }

// ui_kits/marketing-website/BookingSteps.jsx
try { (() => {
// Premier Staff — Numbered booking steps
const BookingSteps = ({
  steps
}) => /*#__PURE__*/React.createElement("section", {
  style: {
    padding: "32px 84px 84px"
  }
}, /*#__PURE__*/React.createElement("div", {
  style: {
    display: "grid",
    gridTemplateColumns: "repeat(3, 1fr)",
    gap: 32
  }
}, steps.map((s, i) => /*#__PURE__*/React.createElement("div", {
  key: i,
  style: {
    borderTop: "1px solid var(--border-strong)",
    paddingTop: 22
  }
}, /*#__PURE__*/React.createElement("div", {
  style: {
    font: "var(--body-xs)",
    letterSpacing: "0.06em",
    textTransform: "uppercase",
    color: "var(--fg-3)",
    marginBottom: 18
  }
}, "STEP ", String(i + 1).padStart(2, "0")), /*#__PURE__*/React.createElement("h3", {
  style: {
    font: "var(--display-4)",
    color: "var(--fg)",
    margin: "0 0 14px",
    letterSpacing: "var(--track-display-wide)"
  }
}, s.title), /*#__PURE__*/React.createElement("p", {
  style: {
    font: "var(--body-md)",
    letterSpacing: "var(--track-snug)",
    color: "var(--fg-2)",
    margin: 0
  }
}, s.body)))));
window.BookingSteps = BookingSteps;
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/marketing-website/BookingSteps.jsx", error: String((e && e.message) || e) }); }

// ui_kits/marketing-website/Buttons.jsx
try { (() => {
// Premier Staff — Buttons (primary gradient + secondary outline w/ ring)
const PrimaryButton = ({
  children,
  onClick,
  theme = "light",
  style
}) => /*#__PURE__*/React.createElement("button", {
  onClick: onClick,
  style: {
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    gap: 10,
    height: 46,
    padding: "0 20px",
    borderRadius: 5,
    font: "400 16px/1 var(--font-body)",
    letterSpacing: "var(--track-loose)",
    cursor: "pointer",
    border: 0,
    background: theme === "dark" ? "#fff" : "linear-gradient(rgb(60,60,60) 0%, rgb(23,23,18) 46%, rgb(23,23,18) 95%)",
    color: theme === "dark" ? "var(--ink-700)" : "#fff",
    transition: "transform 140ms var(--ease-standard), box-shadow 220ms var(--ease-standard)",
    ...style
  },
  onMouseEnter: e => {
    e.currentTarget.style.transform = "translateY(-1px)";
    e.currentTarget.style.boxShadow = "0 4px 4px rgba(0,0,0,0.12)";
  },
  onMouseLeave: e => {
    e.currentTarget.style.transform = "translateY(0)";
    e.currentTarget.style.boxShadow = "none";
  }
}, children);
const SecondaryButton = ({
  children,
  onClick,
  theme = "light",
  style
}) => /*#__PURE__*/React.createElement("button", {
  onClick: onClick,
  style: {
    display: "inline-flex",
    alignItems: "center",
    justifyContent: "center",
    gap: 10,
    height: 46,
    padding: "0 20px",
    borderRadius: 5,
    font: "400 16px/1 var(--font-body)",
    letterSpacing: "var(--track-loose)",
    cursor: "pointer",
    background: "transparent",
    border: `1px solid ${theme === "dark" ? "#fff" : "var(--ink-700)"}`,
    color: theme === "dark" ? "#fff" : "var(--ink-700)",
    boxShadow: "0 0 0 4px rgba(0,0,0,0.15)",
    transition: "background 220ms var(--ease-standard)",
    ...style
  }
}, children);
window.PrimaryButton = PrimaryButton;
window.SecondaryButton = SecondaryButton;
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/marketing-website/Buttons.jsx", error: String((e && e.message) || e) }); }

// ui_kits/marketing-website/FAQ.jsx
try { (() => {
function _extends() { return _extends = Object.assign ? Object.assign.bind() : function (n) { for (var e = 1; e < arguments.length; e++) { var t = arguments[e]; for (var r in t) ({}).hasOwnProperty.call(t, r) && (n[r] = t[r]); } return n; }, _extends.apply(null, arguments); }
// Premier Staff — FAQ accordion
const {
  useState: useStateFAQ
} = React;
const FAQItem = ({
  q,
  a,
  defaultOpen = false
}) => {
  const [open, setOpen] = useStateFAQ(defaultOpen);
  return /*#__PURE__*/React.createElement("div", {
    style: {
      borderBottom: "1px solid var(--border)"
    }
  }, /*#__PURE__*/React.createElement("button", {
    onClick: () => setOpen(!open),
    style: {
      width: "100%",
      padding: "26px 0",
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      gap: 18,
      background: "transparent",
      border: 0,
      cursor: "pointer",
      textAlign: "left"
    }
  }, /*#__PURE__*/React.createElement("h3", {
    style: {
      font: "var(--display-4)",
      color: "var(--fg)",
      letterSpacing: "var(--track-snug)",
      margin: 0,
      flex: 1
    }
  }, q), /*#__PURE__*/React.createElement("div", {
    style: {
      width: 32,
      height: 32,
      borderRadius: 999,
      border: "1px solid var(--border-strong)",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      color: "var(--fg)",
      fontSize: 18,
      flexShrink: 0,
      transform: open ? "rotate(45deg)" : "rotate(0)",
      transition: "transform 220ms var(--ease-standard)"
    }
  }, "+")), open && /*#__PURE__*/React.createElement("p", {
    style: {
      font: "var(--body-md)",
      color: "var(--fg-2)",
      letterSpacing: "var(--track-snug)",
      margin: "0 0 26px",
      maxWidth: 720
    }
  }, a));
};
const FAQ = ({
  items,
  title = "Frequently Asked Questions."
}) => /*#__PURE__*/React.createElement("section", {
  style: {
    padding: "84px 84px"
  }
}, /*#__PURE__*/React.createElement("h2", {
  style: {
    font: "var(--display-3)",
    color: "var(--fg)",
    letterSpacing: "var(--track-display-wide)",
    margin: "0 0 32px"
  }
}, title), /*#__PURE__*/React.createElement("div", null, items.map((it, i) => /*#__PURE__*/React.createElement(FAQItem, _extends({
  key: i
}, it, {
  defaultOpen: i === 0
})))));
window.FAQ = FAQ;
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/marketing-website/FAQ.jsx", error: String((e && e.message) || e) }); }

// ui_kits/marketing-website/Footer.jsx
try { (() => {
// Premier Staff — Editorial footer
const Footer = () => /*#__PURE__*/React.createElement("footer", {
  style: {
    background: "var(--ink-800)",
    color: "rgb(217,217,217)",
    padding: "84px 84px 32px"
  }
}, /*#__PURE__*/React.createElement("div", {
  style: {
    display: "grid",
    gridTemplateColumns: "2fr 1fr 1fr 1fr",
    gap: 48,
    marginBottom: 64
  }
}, /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("img", {
  src: "../../assets/logo-premier-staff.svg",
  alt: "Premier Staff",
  style: {
    height: 38,
    filter: "invert(1) brightness(0.92)",
    marginBottom: 24
  }
}), /*#__PURE__*/React.createElement("p", {
  style: {
    font: "var(--body-md)",
    color: "rgba(217,217,217,0.7)",
    letterSpacing: "var(--track-snug)",
    maxWidth: 360,
    margin: "0 0 24px"
  }
}, "Stress-free executive event staffing in 21 cities nationwide."), /*#__PURE__*/React.createElement(Rating, {
  theme: "dark",
  size: 18
})), [{
  h: "EVENTS",
  links: ["Corporate", "Activations", "Conventions", "Hospitality", "Productions"]
}, {
  h: "LOCATIONS",
  links: ["New York", "Los Angeles", "Miami", "Austin", "Chicago"]
}, {
  h: "COMPANY",
  links: ["About", "Insights", "Careers", "Contact", "Press"]
}].map(col => /*#__PURE__*/React.createElement("div", {
  key: col.h
}, /*#__PURE__*/React.createElement("h4", {
  style: {
    font: "var(--eyebrow)",
    letterSpacing: "0.06em",
    textTransform: "uppercase",
    color: "rgba(217,217,217,0.5)",
    margin: "0 0 18px"
  }
}, col.h), /*#__PURE__*/React.createElement("ul", {
  style: {
    listStyle: "none",
    padding: 0,
    margin: 0,
    display: "flex",
    flexDirection: "column",
    gap: 12
  }
}, col.links.map(l => /*#__PURE__*/React.createElement("li", {
  key: l
}, /*#__PURE__*/React.createElement("a", {
  style: {
    font: "var(--body-md)",
    color: "rgb(217,217,217)",
    letterSpacing: "var(--track-snug)",
    cursor: "pointer"
  }
}, l))))))), /*#__PURE__*/React.createElement("div", {
  style: {
    borderTop: "1px solid rgba(217,217,217,0.12)",
    paddingTop: 24,
    display: "flex",
    justifyContent: "space-between",
    font: "var(--body-xs)",
    color: "rgba(217,217,217,0.5)"
  }
}, /*#__PURE__*/React.createElement("span", null, "\xA9 2025 Premier Staff, LLC"), /*#__PURE__*/React.createElement("span", null, "info@premierstaff.com \xB7 +1 (212) 555-0123")));
window.Footer = Footer;
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/marketing-website/Footer.jsx", error: String((e && e.message) || e) }); }

// ui_kits/marketing-website/Hero.jsx
try { (() => {
// Premier Staff — Hero (left-aligned with photo card)
const Hero = ({
  eyebrow,
  title = "Stress-Free Event Staffing.",
  subtitle = "We provide professional, highly trained event staff for any occasion, ensuring your event runs smoothly and successfully.",
  image = "../../assets/hero-image.png",
  primaryCta = "HIRE STAFF",
  secondaryCta = "SEE PRICING",
  rating = 4.8
}) => /*#__PURE__*/React.createElement("section", {
  style: {
    padding: "84px 84px 64px",
    display: "grid",
    gridTemplateColumns: "1.2fr 0.9fr",
    gap: 48,
    alignItems: "center",
    background: "var(--bg)"
  }
}, /*#__PURE__*/React.createElement("div", null, eyebrow && /*#__PURE__*/React.createElement("div", {
  style: {
    font: "var(--eyebrow)",
    color: "var(--fg-3)",
    marginBottom: 18,
    textTransform: "uppercase"
  }
}, eyebrow), /*#__PURE__*/React.createElement("h1", {
  style: {
    font: "var(--display-1)",
    letterSpacing: "var(--track-display-wide)",
    color: "var(--fg)",
    margin: "0 0 24px",
    maxWidth: 720
  }
}, title), /*#__PURE__*/React.createElement("p", {
  style: {
    font: "var(--body-xl)",
    letterSpacing: "var(--track-snug)",
    color: "var(--fg-2)",
    maxWidth: 520,
    margin: "0 0 32px"
  }
}, subtitle), /*#__PURE__*/React.createElement("div", {
  style: {
    display: "flex",
    gap: 14,
    marginBottom: 28
  }
}, /*#__PURE__*/React.createElement(PrimaryButton, null, primaryCta), /*#__PURE__*/React.createElement(SecondaryButton, null, secondaryCta)), /*#__PURE__*/React.createElement(Rating, {
  score: rating
})), /*#__PURE__*/React.createElement("div", {
  style: {
    position: "relative",
    borderRadius: 6,
    overflow: "hidden",
    aspectRatio: "4/5",
    boxShadow: "0 24px 48px rgba(0,0,0,0.15)"
  }
}, /*#__PURE__*/React.createElement("img", {
  src: image,
  alt: "",
  style: {
    width: "100%",
    height: "100%",
    objectFit: "cover"
  }
})));
window.Hero = Hero;
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/marketing-website/Hero.jsx", error: String((e && e.message) || e) }); }

// ui_kits/marketing-website/HeroCentered.jsx
try { (() => {
// Premier Staff — Centered hero (Enterprise / dark-theme variant)
const HeroCentered = ({
  eyebrow = "ENTERPRISE",
  title = "Premier Staff for Premier Brands.",
  subtitle = "Long-term staffing partnerships for venues, stadiums, conventions, and brand activations across the country.",
  primaryCta = "TALK TO SALES",
  secondaryCta = "OUR LOCATIONS",
  theme = "dark"
}) => /*#__PURE__*/React.createElement("section", {
  style: {
    padding: "120px 84px 96px",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    textAlign: "center",
    background: "var(--bg)"
  }
}, /*#__PURE__*/React.createElement("div", {
  style: {
    font: "var(--eyebrow)",
    color: "var(--fg-3)",
    marginBottom: 22,
    textTransform: "uppercase"
  }
}, eyebrow), /*#__PURE__*/React.createElement("h1", {
  style: {
    font: "var(--display-1)",
    letterSpacing: "var(--track-display-wide)",
    color: "var(--fg)",
    margin: "0 0 24px",
    maxWidth: 980
  }
}, title), /*#__PURE__*/React.createElement("p", {
  style: {
    font: "var(--body-xl)",
    letterSpacing: "var(--track-snug)",
    color: "var(--fg-2)",
    maxWidth: 660,
    margin: "0 0 36px"
  }
}, subtitle), /*#__PURE__*/React.createElement("div", {
  style: {
    display: "flex",
    gap: 14
  }
}, /*#__PURE__*/React.createElement(PrimaryButton, {
  theme: theme
}, primaryCta), /*#__PURE__*/React.createElement(SecondaryButton, {
  theme: theme
}, secondaryCta)));
window.HeroCentered = HeroCentered;
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/marketing-website/HeroCentered.jsx", error: String((e && e.message) || e) }); }

// ui_kits/marketing-website/Nav.jsx
try { (() => {
// Premier Staff — Nav (sticky, themed light/dark)
const Nav = ({
  active = "home",
  onNavigate,
  theme = "light",
  onToggleTheme
}) => {
  const links = [{
    id: "locations",
    label: "LOCATIONS"
  }, {
    id: "events",
    label: "EVENTS"
  }, {
    id: "enterprise",
    label: "ENTERPRISE"
  }];
  return /*#__PURE__*/React.createElement("header", {
    style: {
      position: "sticky",
      top: 0,
      zIndex: 50,
      height: 82,
      background: theme === "dark" ? "rgba(14,14,14,0.92)" : "rgba(252,251,250,0.92)",
      backdropFilter: "blur(20px)",
      borderBottom: "1px solid var(--border)",
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      padding: "0 84px"
    }
  }, /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: 64
    }
  }, /*#__PURE__*/React.createElement("a", {
    onClick: () => onNavigate?.("home"),
    style: {
      cursor: "pointer",
      display: "flex",
      alignItems: "center",
      color: theme === "dark" ? "rgb(217,217,217)" : "var(--ink-700)"
    }
  }, /*#__PURE__*/React.createElement("img", {
    src: "../../assets/logo-premier-staff.svg",
    alt: "Premier Staff",
    style: {
      height: 36,
      color: "currentColor",
      filter: theme === "dark" ? "invert(1) brightness(0.92)" : "none"
    }
  })), /*#__PURE__*/React.createElement("nav", {
    style: {
      display: "flex",
      gap: 18
    }
  }, links.map(l => /*#__PURE__*/React.createElement("a", {
    key: l.id,
    onClick: () => onNavigate?.(l.id === "enterprise" ? "enterprise" : "home"),
    style: {
      cursor: "pointer",
      font: "var(--label-md)",
      letterSpacing: "var(--track-snug)",
      color: theme === "dark" ? "rgb(217,217,217)" : "var(--ink-700)",
      opacity: active === l.id ? 1 : 0.85
    }
  }, l.label)))), /*#__PURE__*/React.createElement("div", {
    style: {
      display: "flex",
      alignItems: "center",
      gap: 20
    }
  }, /*#__PURE__*/React.createElement("a", {
    onClick: () => onNavigate?.("pricing"),
    style: {
      cursor: "pointer",
      font: "var(--label-md)",
      color: theme === "dark" ? "rgb(217,217,217)" : "var(--ink-700)"
    }
  }, "PRICING"), /*#__PURE__*/React.createElement("button", {
    className: "btn",
    onClick: () => onNavigate?.("contact"),
    style: {
      height: 40,
      padding: "0 14px",
      fontSize: 16,
      borderRadius: 5,
      background: theme === "dark" ? "#fff" : "var(--ink-700)",
      color: theme === "dark" ? "var(--ink-700)" : "#fff",
      border: 0,
      cursor: "pointer"
    }
  }, "CONTACT US")));
};
window.Nav = Nav;
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/marketing-website/Nav.jsx", error: String((e && e.message) || e) }); }

// ui_kits/marketing-website/Rating.jsx
try { (() => {
// Premier Staff — Star rating row
const StarRow = ({
  count = 5,
  size = 20,
  color = "rgb(181,150,70)"
}) => /*#__PURE__*/React.createElement("div", {
  style: {
    display: "flex",
    gap: 2
  }
}, Array.from({
  length: count
}).map((_, i) => /*#__PURE__*/React.createElement("svg", {
  key: i,
  width: size,
  height: size,
  viewBox: "0 0 24 24",
  fill: color
}, /*#__PURE__*/React.createElement("path", {
  d: "M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"
}))));
const Rating = ({
  score = 4.8,
  label = "Average Client Rating",
  theme = "light",
  size = 20
}) => /*#__PURE__*/React.createElement("div", {
  style: {
    display: "flex",
    alignItems: "center",
    gap: 8
  }
}, /*#__PURE__*/React.createElement("span", {
  style: {
    font: `700 ${size * 0.9}px var(--font-body)`,
    letterSpacing: "var(--track-snug)",
    color: theme === "dark" ? "rgb(228,228,228)" : "var(--ink-700)"
  }
}, score), /*#__PURE__*/React.createElement(StarRow, {
  size: size,
  color: theme === "dark" ? "rgb(228,228,228)" : "rgb(181,150,70)"
}), /*#__PURE__*/React.createElement("span", {
  style: {
    font: "var(--body-xs)",
    letterSpacing: "var(--track-snug)",
    color: theme === "dark" ? "rgba(217,217,217,0.5)" : "rgba(23,23,18,0.5)"
  }
}, label));
window.StarRow = StarRow;
window.Rating = Rating;
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/marketing-website/Rating.jsx", error: String((e && e.message) || e) }); }

// ui_kits/marketing-website/Review.jsx
try { (() => {
// Premier Staff — Testimonial / pull-quote
const Review = ({
  quote = "Working with Premier Staff was an absolute breeze. Their team made the entire process seamless and effortless.",
  name = "Shanita Castle",
  role = "Brand Activation Manager",
  avatar,
  stars = 5
}) => /*#__PURE__*/React.createElement("div", {
  style: {
    background: "var(--bg)",
    borderRadius: 12,
    padding: 32,
    border: "1px solid var(--border)"
  }
}, /*#__PURE__*/React.createElement(StarRow, {
  count: stars,
  size: 16
}), /*#__PURE__*/React.createElement("p", {
  style: {
    font: "var(--display-4)",
    letterSpacing: "var(--track-snug)",
    color: "var(--fg)",
    margin: "16px 0 24px"
  }
}, "\"", quote, "\""), /*#__PURE__*/React.createElement("div", {
  style: {
    display: "flex",
    alignItems: "center",
    gap: 12
  }
}, /*#__PURE__*/React.createElement("div", {
  style: {
    width: 40,
    height: 40,
    borderRadius: 999,
    background: avatar ? `url(${avatar}) center/cover` : "var(--ink-450)"
  }
}), /*#__PURE__*/React.createElement("div", null, /*#__PURE__*/React.createElement("div", {
  style: {
    font: "600 14px var(--font-body)",
    color: "var(--fg)"
  }
}, name), /*#__PURE__*/React.createElement("div", {
  style: {
    font: "var(--body-xs)",
    color: "var(--fg-3)"
  }
}, role))));
window.Review = Review;
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/marketing-website/Review.jsx", error: String((e && e.message) || e) }); }

// ui_kits/marketing-website/SectionTitle.jsx
try { (() => {
// Premier Staff — Section title (Playfair + Roboto subhead)
const SectionTitle = ({
  eyebrow,
  title,
  subtitle,
  align = "left"
}) => /*#__PURE__*/React.createElement("div", {
  style: {
    textAlign: align,
    padding: "84px 84px 32px",
    maxWidth: align === "center" ? "100%" : 720
  }
}, eyebrow && /*#__PURE__*/React.createElement("div", {
  style: {
    font: "var(--eyebrow)",
    color: "var(--fg-3)",
    textTransform: "uppercase",
    marginBottom: 16
  }
}, eyebrow), /*#__PURE__*/React.createElement("h2", {
  style: {
    font: "var(--display-3)",
    letterSpacing: "var(--track-display-wide)",
    color: "var(--fg)",
    margin: 0
  }
}, title), subtitle && /*#__PURE__*/React.createElement("p", {
  style: {
    font: "var(--body-lg)",
    color: "var(--fg-2)",
    letterSpacing: "var(--track-snug)",
    marginTop: 18,
    maxWidth: 620
  }
}, subtitle));
window.SectionTitle = SectionTitle;
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/marketing-website/SectionTitle.jsx", error: String((e && e.message) || e) }); }

// ui_kits/marketing-website/TrustedBy.jsx
try { (() => {
// Premier Staff — Trusted-by client wordmark strip
const TrustedBy = ({
  theme = "dark",
  clients = ["NETFLIX", "spotify", "CONVERSE", "Stagecoach", "UNIQLO", "BUDWEISER", "FANATICS"]
}) => /*#__PURE__*/React.createElement("section", {
  style: {
    padding: "56px 84px",
    background: theme === "dark" ? "var(--ink-800)" : "var(--ink-700)",
    color: theme === "dark" ? "rgb(217,217,217)" : "rgb(217,217,217)"
  }
}, /*#__PURE__*/React.createElement("div", {
  style: {
    font: "600 12px var(--font-body)",
    letterSpacing: "0.18em",
    textTransform: "uppercase",
    textAlign: "center",
    color: "rgba(217,217,217,0.7)",
    marginBottom: 28
  }
}, "Trusted By"), /*#__PURE__*/React.createElement("div", {
  style: {
    display: "flex",
    justifyContent: "center",
    alignItems: "center",
    gap: 64,
    flexWrap: "wrap",
    opacity: 0.85
  }
}, clients.map(c => /*#__PURE__*/React.createElement("span", {
  key: c,
  style: {
    font: "600 26px var(--font-display)",
    letterSpacing: "0.04em",
    color: "rgb(228,228,228)"
  }
}, c))));
window.TrustedBy = TrustedBy;
})(); } catch (e) { __ds_ns.__errors.push({ path: "ui_kits/marketing-website/TrustedBy.jsx", error: String((e && e.message) || e) }); }

})();
