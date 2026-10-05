import { FormEvent, ReactNode, useEffect, useMemo, useState } from "react";

type View =
  | "login"
  | "register"
  | "forgot"
  | "home"
  | "results"
  | "seats"
  | "checkout"
  | "confirmation"
  | "bookings";

type User = { name: string; email: string; mobile: string; password: string };
type Search = {
  from: string;
  to: string;
  journeyDate: string;
  returnDate: string;
  passengers: number;
};
type Bus = {
  id: number;
  operator: string;
  type: string;
  departure: string;
  arrival: string;
  duration: string;
  boarding: string;
  dropping: string;
  seats: number;
  price: number;
  rating: number;
  ratings: number;
  amenities: string[];
  tag?: string;
};
type Booking = {
  id: string;
  bus: Bus;
  search: Search;
  seats: string[];
  passengerNames: string[];
  total: number;
  bookedAt: string;
  status: "Confirmed" | "Cancelled";
};

const cities = ["Bengaluru", "Chennai", "Coimbatore", "Hyderabad", "Kochi", "Madurai", "Mysuru", "Pondicherry"];
const tomorrow = new Date(Date.now() + 86400000).toISOString().split("T")[0];
const futureDate = new Date(Date.now() + 4 * 86400000).toISOString().split("T")[0];

const buses: Bus[] = [
  {
    id: 1,
    operator: "Orange Line Express",
    type: "Volvo A/C Sleeper (2+1)",
    departure: "21:30",
    arrival: "05:30",
    duration: "8h 00m",
    boarding: "Koyambedu",
    dropping: "Madiwala",
    seats: 17,
    price: 899,
    rating: 4.7,
    ratings: 1248,
    amenities: ["Wi-Fi", "Charging", "Blanket", "Live tracking"],
    tag: "Popular choice",
  },
  {
    id: 2,
    operator: "Intercity SmartBus",
    type: "A/C Seater (2+2)",
    departure: "06:15",
    arrival: "12:45",
    duration: "6h 30m",
    boarding: "Guindy",
    dropping: "Silk Board",
    seats: 23,
    price: 649,
    rating: 4.5,
    ratings: 892,
    amenities: ["Wi-Fi", "Water bottle", "Charging"],
    tag: "Lowest price",
  },
  {
    id: 3,
    operator: "Greenway Travels",
    type: "BharatBenz A/C Sleeper (2+1)",
    departure: "22:45",
    arrival: "06:00",
    duration: "7h 15m",
    boarding: "Koyambedu",
    dropping: "Electronic City",
    seats: 9,
    price: 1049,
    rating: 4.8,
    ratings: 674,
    amenities: ["Blanket", "Reading light", "Charging", "Live tracking"],
    tag: "Top rated",
  },
  {
    id: 4,
    operator: "KPN Roadlines",
    type: "Non A/C Sleeper (2+1)",
    departure: "20:15",
    arrival: "04:45",
    duration: "8h 30m",
    boarding: "Porur",
    dropping: "Majestic",
    seats: 14,
    price: 729,
    rating: 4.2,
    ratings: 532,
    amenities: ["Water bottle", "Reading light"],
  },
];

const iconPaths: Record<string, ReactNode> = {
  bus: <><path d="M6 17h12M7 17v2M17 17v2M5 14V6a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v8a3 3 0 0 1-3 3H8a3 3 0 0 1-3-3Z"/><path d="M5 10h14M8 13h.01M16 13h.01"/></>,
  user: <><circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/></>,
  map: <><circle cx="12" cy="10" r="3"/><path d="M19 10c0 5-7 11-7 11S5 15 5 10a7 7 0 1 1 14 0Z"/></>,
  calendar: <><path d="M6 2v3M18 2v3M3 9h18"/><rect x="3" y="4" width="18" height="18" rx="3"/></>,
  users: <><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/></>,
  arrow: <><path d="M5 12h14M15 8l4 4-4 4"/></>,
  swap: <><path d="m7 7 3-3 3 3M10 4v11M17 17l-3 3-3-3M14 20V9"/></>,
  clock: <><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></>,
  star: <path d="m12 2.5 2.9 5.88 6.49.94-4.7 4.58 1.11 6.47L12 17.32l-5.8 3.05 1.11-6.47-4.7-4.58 6.49-.94L12 2.5Z"/>,
  shield: <><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z"/><path d="m9 12 2 2 4-4"/></>,
  ticket: <><path d="M3 7a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v3a2 2 0 0 0 0 4v3a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-3a2 2 0 0 0 0-4V7Z"/><path d="M13 5v2M13 17v2M13 10v4"/></>,
  chevron: <path d="m9 18 6-6-6-6"/>,
  check: <path d="m5 12 4 4L19 6"/>,
  back: <><path d="m15 18-6-6 6-6"/><path d="M9 12h10"/></>,
  card: <><rect x="2" y="5" width="20" height="14" rx="2"/><path d="M2 10h20M6 15h4"/></>,
  logout: <><path d="M10 17l5-5-5-5M15 12H3"/><path d="M15 4h4a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-4"/></>,
  search: <><circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/></>,
};

function Icon({ name, size = 20, className = "" }: { name: string; size?: number; className?: string }) {
  return <svg className={className} width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{iconPaths[name]}</svg>;
}

function Field({ label, icon, error, children }: { label: string; icon?: string; error?: string; children: ReactNode }) {
  return <label className="field"><span className="field-label">{label}</span><span className={`field-control ${error ? "field-error" : ""}`}>{icon && <Icon name={icon} size={18} />}{children}</span>{error && <span className="error-text">{error}</span>}</label>;
}

function AppHeader({ view, setView, user, logout }: { view: View; setView: (v: View) => void; user: User; logout: () => void }) {
  return <header className="app-header">
    <button className="brand" onClick={() => setView("home")} aria-label="Go to home"><span className="brand-mark"><Icon name="bus" /></span><span>roam<span>bus</span></span></button>
    <nav className="main-nav" aria-label="Main navigation">
      <button className={view === "home" || view === "results" ? "active" : ""} onClick={() => setView("home")}>Search buses</button>
      <button className={view === "bookings" ? "active" : ""} onClick={() => setView("bookings")}>My bookings</button>
      <button className="user-menu" onClick={() => setView("bookings")}><span>{user.name.charAt(0).toUpperCase()}</span><span className="user-copy"><small>Welcome</small>{user.name.split(" ")[0]}</span></button>
      <button className="icon-button" onClick={logout} aria-label="Log out" title="Log out"><Icon name="logout" size={19} /></button>
    </nav>
  </header>;
}

function AuthShell({ mode, setView, onAuth }: { mode: "login" | "register" | "forgot"; setView: (v: View) => void; onAuth: (user: User) => void }) {
  const [values, setValues] = useState({ name: "", email: "", mobile: "", password: "", confirm: "", identifier: "" });
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [notice, setNotice] = useState("");
  const update = (key: string, value: string) => { setValues(v => ({ ...v, [key]: value })); setErrors(e => ({ ...e, [key]: "" })); };

  const submit = (event: FormEvent) => {
    event.preventDefault();
    const next: Record<string, string> = {};
    if (mode === "register") {
      if (values.name.trim().length < 3) next.name = "Enter your full name";
      if (!/^\S+@\S+\.\S+$/.test(values.email)) next.email = "Enter a valid email";
      if (!/^[6-9]\d{9}$/.test(values.mobile)) next.mobile = "Enter a valid 10-digit mobile number";
      if (values.password.length < 6) next.password = "Use at least 6 characters";
      if (values.confirm !== values.password) next.confirm = "Passwords do not match";
      if (Object.keys(next).length) return setErrors(next);
      const user = { name: values.name.trim(), email: values.email.toLowerCase(), mobile: values.mobile, password: values.password };
      const users: User[] = JSON.parse(localStorage.getItem("roambus_users") || "[]");
      if (users.some(item => item.email === user.email || item.mobile === user.mobile)) return setErrors({ email: "An account with these details already exists" });
      localStorage.setItem("roambus_users", JSON.stringify([...users, user]));
      onAuth(user);
    } else if (mode === "login") {
      if (!values.identifier.trim()) next.identifier = "Enter your email or mobile number";
      if (!values.password) next.password = "Enter your password";
      if (Object.keys(next).length) return setErrors(next);
      const users: User[] = JSON.parse(localStorage.getItem("roambus_users") || "[]");
      const user = users.find(item => (item.email === values.identifier.toLowerCase() || item.mobile === values.identifier) && item.password === values.password);
      if (!user) return setErrors({ identifier: "Account details do not match. Try the demo account." });
      onAuth(user);
    } else {
      if (!values.identifier.trim()) return setErrors({ identifier: "Enter your registered email or mobile" });
      setNotice("If an account exists, password reset instructions have been sent.");
    }
  };

  return <main className="auth-page">
    <section className="auth-visual">
      <div className="auth-top"><span className="brand-mark"><Icon name="bus" /></span><span className="brand-name">roam<span>bus</span></span></div>
      <div className="route-art" aria-hidden="true"><span className="route-dot start" /><span className="route-line" /><span className="route-bus"><Icon name="bus" size={26} /></span><span className="route-dot end" /></div>
      <div className="auth-message">
        <span className="eyebrow light">TRAVEL, SIMPLIFIED</span>
        <h1>Your journey starts with a better way to book.</h1>
        <p>Compare trusted operators, choose your perfect seat, and travel with confidence.</p>
        <div className="trust-row"><span><Icon name="shield" />Secure booking</span><span><Icon name="ticket" />Instant confirmation</span></div>
      </div>
    </section>
    <section className="auth-form-wrap">
      <form className="auth-card" onSubmit={submit}>
        <div className="mobile-brand"><span className="brand-mark"><Icon name="bus" /></span><span className="brand-name">Your<span>bus</span></span></div>
        <span className="eyebrow">{mode === "register" ? "CREATE ACCOUNT" : mode === "forgot" ? "ACCOUNT RECOVERY" : "WELCOME BACK"}</span>
        <h2>{mode === "register" ? "Join the journey" : mode === "forgot" ? "Reset your password" : "Sign in to continue"}</h2>
        <p className="form-intro">{mode === "register" ? "Book faster and keep every trip in one place." : mode === "forgot" ? "We’ll send recovery instructions to your registered contact." : "Your next comfortable ride is only a few clicks away."}</p>
        {notice && <div className="success-note"><Icon name="check" size={18} />{notice}</div>}
        {mode === "register" && <Field label="Full name" icon="user" error={errors.name}><input value={values.name} onChange={e => update("name", e.target.value)} placeholder="Arun Kumar" /></Field>}
        <Field label={mode === "register" ? "Email address" : "Email or mobile number"} icon="user" error={errors[mode === "register" ? "email" : "identifier"]}><input type={mode === "register" ? "email" : "text"} value={mode === "register" ? values.email : values.identifier} onChange={e => update(mode === "register" ? "email" : "identifier", e.target.value)} placeholder={mode === "register" ? "you@example.com" : "you@example.com"} /></Field>
        {mode === "register" && <Field label="Mobile number" error={errors.mobile}><span className="prefix">+91</span><input value={values.mobile} onChange={e => update("mobile", e.target.value.replace(/\D/g, "").slice(0, 10))} placeholder="98765 43210" /></Field>}
        {mode !== "forgot" && <Field label="Password" icon="shield" error={errors.password}><input type="password" value={values.password} onChange={e => update("password", e.target.value)} placeholder="••••••••" /></Field>}
        {mode === "register" && <Field label="Confirm password" icon="shield" error={errors.confirm}><input type="password" value={values.confirm} onChange={e => update("confirm", e.target.value)} placeholder="••••••••" /></Field>}
        {mode === "login" && <button type="button" className="text-link forgot" onClick={() => setView("forgot")}>Forgot password?</button>}
        <button className="primary-button full" type="submit">{mode === "register" ? "Create account" : mode === "forgot" ? "Send reset link" : "Sign in"}<Icon name="arrow" size={18} /></button>
        {mode === "login" && <button className="demo-button" type="button" onClick={() => { update("identifier", "demo@roambus.in"); update("password", "demo123"); }}>Use demo account</button>}
        <p className="auth-switch">{mode === "register" ? "Already have an account?" : mode === "forgot" ? "Remember your password?" : "New to Roambus?"} <button type="button" onClick={() => setView(mode === "register" || mode === "forgot" ? "login" : "register")}>{mode === "register" || mode === "forgot" ? "Sign in" : "Create an account"}</button></p>
      </form>
    </section>
  </main>;
}

function SearchForm({ initial, onSearch }: { initial: Search; onSearch: (search: Search) => void }) {
  const [search, setSearch] = useState(initial);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const update = (key: keyof Search, value: string | number) => { setSearch(s => ({ ...s, [key]: value })); setErrors({}); };
  const submit = (event: FormEvent) => {
    event.preventDefault();
    const next: Record<string, string> = {};
    if (!search.from) next.from = "Choose a departure city";
    if (!search.to) next.to = "Choose a destination";
    if (search.from && search.from === search.to) next.to = "Destination must be different";
    if (!search.journeyDate || search.journeyDate < tomorrow) next.journeyDate = "Choose a future date";
    if (search.returnDate && search.returnDate < search.journeyDate) next.returnDate = "Return must be after departure";
    if (search.passengers < 1 || search.passengers > 6) next.passengers = "Choose 1–6 passengers";
    if (Object.keys(next).length) return setErrors(next);
    onSearch(search);
  };
  return <form className="search-panel" onSubmit={submit}>
    <div className="search-grid">
      <Field label="From" icon="map" error={errors.from}><select value={search.from} onChange={e => update("from", e.target.value)}><option value="">Leaving from</option>{cities.map(city => <option key={city}>{city}</option>)}</select></Field>
      <button type="button" className="swap-button" onClick={() => setSearch(s => ({ ...s, from: s.to, to: s.from }))} aria-label="Swap cities"><Icon name="swap" size={17} /></button>
      <Field label="To" icon="map" error={errors.to}><select value={search.to} onChange={e => update("to", e.target.value)}><option value="">Going to</option>{cities.map(city => <option key={city}>{city}</option>)}</select></Field>
      <Field label="Journey date" icon="calendar" error={errors.journeyDate}><input type="date" min={tomorrow} value={search.journeyDate} onChange={e => update("journeyDate", e.target.value)} /></Field>
      <Field label="Return date" icon="calendar" error={errors.returnDate}><input type="date" min={search.journeyDate || tomorrow} value={search.returnDate} onChange={e => update("returnDate", e.target.value)} /></Field>
      <Field label="Passengers" icon="users" error={errors.passengers}><select value={search.passengers} onChange={e => update("passengers", Number(e.target.value))}>{[1,2,3,4,5,6].map(n => <option key={n} value={n}>{n} {n === 1 ? "Passenger" : "Passengers"}</option>)}</select></Field>
      <button className="primary-button search-button" type="submit"><Icon name="search" size={19} />Search buses</button>
    </div>
  </form>;
}

function Home({ user, search, onSearch }: { user: User; search: Search; onSearch: (s: Search) => void }) {
  return <main>
    <section className="hero">
      <div className="hero-orb orb-one" /><div className="hero-orb orb-two" />
      <div className="hero-content">
        <span className="eyebrow light">HELLO, {user.name.split(" ")[0].toUpperCase()}</span>
        <h1>Where would you like to go?</h1>
        <p>Book reliable bus travel across South India, without the usual hassle.</p>
      </div>
    </section>
    <div className="home-content">
      <SearchForm initial={search} onSearch={onSearch} />
      <section className="benefits">
        <div className="benefit-heading"><span className="eyebrow">WHY ROAMBUS</span><h2>Travel made refreshingly simple</h2></div>
        <div className="benefit-grid">
          <article><span className="feature-icon coral"><Icon name="search" /></span><h3>Compare with clarity</h3><p>See prices, timings, ratings, and amenities side by side.</p></article>
          <article><span className="feature-icon teal"><Icon name="ticket" /></span><h3>Pick your exact seat</h3><p>Choose the seat you want with our live interactive seat map.</p></article>
          <article><span className="feature-icon gold"><Icon name="shield" /></span><h3>Book with confidence</h3><p>Secure checkout, instant tickets, and reliable trip support.</p></article>
        </div>
      </section>
    </div>
  </main>;
}

function Results({ search, onModify, onSelect }: { search: Search; onModify: () => void; onSelect: (bus: Bus) => void }) {
  const [sort, setSort] = useState("recommended");
  const [acOnly, setAcOnly] = useState(false);
  const [sleeperOnly, setSleeperOnly] = useState(false);
  const [compare, setCompare] = useState<number[]>([]);
  const visible = useMemo(() => {
    let list = buses.filter(bus => (!acOnly || bus.type.includes("A/C")) && (!sleeperOnly || bus.type.includes("Sleeper")));
    if (sort === "price") list = [...list].sort((a,b) => a.price - b.price);
    if (sort === "rating") list = [...list].sort((a,b) => b.rating - a.rating);
    if (sort === "departure") list = [...list].sort((a,b) => a.departure.localeCompare(b.departure));
    return list;
  }, [sort, acOnly, sleeperOnly]);
  const dateLabel = new Date(`${search.journeyDate}T12:00:00`).toLocaleDateString("en-IN", { weekday: "short", day: "numeric", month: "short" });
  return <main className="results-page">
    <section className="route-summary"><div><span>{search.from}</span><Icon name="arrow" /><span>{search.to}</span></div><p><Icon name="calendar" size={16} />{dateLabel}<b>·</b><Icon name="users" size={16} />{search.passengers} {search.passengers === 1 ? "passenger" : "passengers"}</p><button onClick={onModify}>Modify search</button></section>
    <div className="results-layout">
      <aside className="filters">
        <div className="filter-title"><h3>Filters</h3><button onClick={() => { setAcOnly(false); setSleeperOnly(false); }}>Reset</button></div>
        <div className="filter-group"><h4>Bus type</h4><label><input type="checkbox" checked={acOnly} onChange={e => setAcOnly(e.target.checked)} /><span>A/C buses</span><small>3</small></label><label><input type="checkbox" checked={sleeperOnly} onChange={e => setSleeperOnly(e.target.checked)} /><span>Sleeper</span><small>3</small></label></div>
        <div className="filter-group"><h4>Departure time</h4><div className="time-options"><button><span>☼</span>Before 12 PM</button><button><span>◐</span>12–6 PM</button><button><span>☾</span>After 6 PM</button></div></div>
        <div className="filter-assurance"><Icon name="shield" /><div><b>Roambus assurance</b><p>Verified operators and secure payments</p></div></div>
      </aside>
      <section className="result-list">
        <div className="results-toolbar"><div><h2>{visible.length} buses found</h2><p>Showing the best options for your trip</p></div><label>Sort by <select value={sort} onChange={e => setSort(e.target.value)}><option value="recommended">Recommended</option><option value="price">Lowest price</option><option value="rating">Top rated</option><option value="departure">Departure</option></select></label></div>
        {compare.length > 1 && <div className="compare-bar"><span><Icon name="check" />{compare.length} buses selected for comparison</span><button onClick={() => setSort("price")}>Compare prices</button></div>}
        {visible.map(bus => <article className="bus-card" key={bus.id}>
          <div className="bus-card-top">
            <div className="operator"><div className={`operator-logo logo-${bus.id}`}>{bus.operator.split(" ").map(w => w[0]).slice(0,2).join("")}</div><div>{bus.tag && <span className="bus-tag">{bus.tag}</span>}<h3>{bus.operator}</h3><p>{bus.type}</p></div></div>
            <div className="rating"><Icon name="star" size={14} /><b>{bus.rating}</b><span>{bus.ratings.toLocaleString("en-IN")} ratings</span></div>
          </div>
          <div className="bus-details">
            <div className="timeline"><div><strong>{bus.departure}</strong><span>{bus.boarding}</span></div><div className="duration"><span>{bus.duration}</span><i /><small>Direct</small></div><div><strong>{bus.arrival}</strong><span>{bus.dropping}</span></div></div>
            <div className="price"><span>Starts from</span><strong>₹{bus.price.toLocaleString("en-IN")}</strong><small>per seat</small></div>
          </div>
          <div className="bus-card-bottom"><div className="amenities">{bus.amenities.slice(0,4).map(item => <span key={item}>{item}</span>)}</div><div className="availability"><span><i />{bus.seats} seats available</span><button className="primary-button compact" onClick={() => onSelect(bus)}>View seats<Icon name="chevron" size={16} /></button></div></div>
          <label className="compare-check"><input type="checkbox" checked={compare.includes(bus.id)} onChange={e => setCompare(ids => e.target.checked ? [...ids, bus.id] : ids.filter(id => id !== bus.id))} />Add to compare</label>
        </article>)}
      </section>
    </div>
  </main>;
}

const seatRows = ["A", "B", "C", "D", "E", "F", "G", "H"];
const bookedSeats = ["A2", "B3", "C1", "D4", "E2", "F3", "H1"];
const femaleSeats = ["B1", "E4"];

function SeatSelection({ bus, search, onBack, onContinue }: { bus: Bus; search: Search; onBack: () => void; onContinue: (seats: string[]) => void }) {
  const [selected, setSelected] = useState<string[]>([]);
  const toggle = (seat: string) => {
    if (bookedSeats.includes(seat) || femaleSeats.includes(seat)) return;
    setSelected(items => items.includes(seat) ? items.filter(item => item !== seat) : items.length < search.passengers ? [...items, seat] : items);
  };
  const total = bus.price * selected.length;
  return <main className="step-page">
    <div className="step-header"><button className="back-button" onClick={onBack}><Icon name="back" />Back to buses</button><div className="steps"><span className="active"><b>1</b>Select seats</span><i /><span><b>2</b>Passenger details</span><i /><span><b>3</b>Payment</span></div></div>
    <div className="seat-layout">
      <section className="seat-main">
        <div className="section-heading"><div><span className="eyebrow">CHOOSE YOUR SEATS</span><h1>Make yourself comfortable</h1><p>Select {search.passengers} {search.passengers === 1 ? "seat" : "seats"} for this journey.</p></div><div className="seat-legend"><span><i className="available" />Available</span><span><i className="selected" />Selected</span><span><i className="female" />Women only</span><span><i className="booked" />Booked</span></div></div>
        <div className="bus-layout">
          <div className="driver"><span>Front</span><div>◯</div></div>
          <div className="seats-grid">
            {seatRows.map(row => <div className="seat-row" key={row}><span>{row}</span>{[1,2,3,4].map(number => { const seat = `${row}${number}`; const state = bookedSeats.includes(seat) ? "booked" : femaleSeats.includes(seat) ? "female" : selected.includes(seat) ? "selected" : ""; return <button key={seat} className={`${state} ${number === 3 ? "aisle" : ""}`} onClick={() => toggle(seat)} aria-label={`Seat ${seat}, ${state || "available"}`}><span>{seat}</span></button>; })}</div>)}
          </div>
          <div className="bus-rear">Rear</div>
        </div>
      </section>
      <aside className="trip-card">
        <span className="eyebrow">YOUR TRIP</span><div className="trip-operator"><div className={`operator-logo logo-${bus.id}`}>{bus.operator.slice(0,2).toUpperCase()}</div><div><h3>{bus.operator}</h3><p>{bus.type}</p></div></div>
        <div className="trip-route"><div><b>{bus.departure}</b><span>{search.from}</span><small>{bus.boarding}</small></div><i><Icon name="bus" size={17} /></i><div><b>{bus.arrival}</b><span>{search.to}</span><small>{bus.dropping}</small></div></div>
        <div className="trip-date"><Icon name="calendar" size={17} /><span>{new Date(`${search.journeyDate}T12:00:00`).toLocaleDateString("en-IN", { weekday: "long", day: "numeric", month: "long" })}</span></div>
        <div className="selected-summary"><div><span>Selected seats</span><b>{selected.length ? selected.join(", ") : "None yet"}</b></div><div><span>Fare ({selected.length} × ₹{bus.price})</span><b>₹{total.toLocaleString("en-IN")}</b></div></div>
        <div className="total-row"><span>Total amount</span><strong>₹{total.toLocaleString("en-IN")}</strong></div>
        {selected.length < search.passengers && <p className="seat-hint">Select {search.passengers - selected.length} more {search.passengers - selected.length === 1 ? "seat" : "seats"} to continue</p>}
        <button className="primary-button full" disabled={selected.length !== search.passengers} onClick={() => onContinue(selected)}>Continue<Icon name="arrow" size={18} /></button>
        <p className="safe-note"><Icon name="shield" size={15} />Your seats are held for 10 minutes</p>
      </aside>
    </div>
  </main>;
}

function Checkout({ bus, search, seats, user, onBack, onComplete }: { bus: Bus; search: Search; seats: string[]; user: User; onBack: () => void; onComplete: (booking: Booking) => void }) {
  const [stage, setStage] = useState<"details" | "payment">("details");
  const [names, setNames] = useState(seats.map((_, i) => i === 0 ? user.name : ""));
  const [contact, setContact] = useState({ email: user.email, mobile: user.mobile });
  const [payment, setPayment] = useState({ card: "", expiry: "", cvv: "", name: user.name });
  const [error, setError] = useState("");
  const base = bus.price * seats.length;
  const fee = Math.round(base * 0.04);
  const total = base + fee;
  const continueToPayment = (event: FormEvent) => {
    event.preventDefault();
    if (names.some(name => name.trim().length < 2)) return setError("Enter the name of every passenger.");
    if (!/^\S+@\S+\.\S+$/.test(contact.email) || !/^[6-9]\d{9}$/.test(contact.mobile)) return setError("Enter valid contact details.");
    setError(""); setStage("payment");
  };
  const pay = (event: FormEvent) => {
    event.preventDefault();
    if (payment.card.replace(/\s/g, "").length !== 16 || !/^\d{2}\/\d{2}$/.test(payment.expiry) || payment.cvv.length !== 3 || payment.name.trim().length < 2) return setError("Check your card details and try again.");
    const booking: Booking = { id: `RB${Date.now().toString().slice(-8)}`, bus, search, seats, passengerNames: names, total, bookedAt: new Date().toISOString(), status: "Confirmed" };
    onComplete(booking);
  };
  return <main className="step-page">
    <div className="step-header"><button className="back-button" onClick={stage === "payment" ? () => setStage("details") : onBack}><Icon name="back" />{stage === "payment" ? "Passenger details" : "Seat selection"}</button><div className="steps"><span className="done"><b><Icon name="check" size={14} /></b>Select seats</span><i /><span className={stage === "details" ? "active" : "done"}><b>{stage === "payment" ? <Icon name="check" size={14} /> : "2"}</b>Passenger details</span><i /><span className={stage === "payment" ? "active" : ""}><b>3</b>Payment</span></div></div>
    <div className="checkout-layout">
      <section className="checkout-main">
        {stage === "details" ? <form onSubmit={continueToPayment}>
          <div className="section-heading"><div><span className="eyebrow">PASSENGER DETAILS</span><h1>Who’s travelling?</h1><p>Enter names exactly as they appear on a valid ID.</p></div></div>
          <div className="form-card">{seats.map((seat, index) => <div className="passenger-row" key={seat}><span className="passenger-number">{index + 1}</span><Field label={`Passenger ${index + 1} · Seat ${seat}`} icon="user"><input value={names[index]} onChange={e => setNames(items => items.map((name, i) => i === index ? e.target.value : name))} placeholder="Full name" /></Field><Field label="Age"><input type="number" min="1" max="100" placeholder="Age" /></Field></div>)}</div>
          <div className="form-card contact-card"><h3>Booking contact</h3><p>Your ticket and trip updates will be sent here.</p><div className="two-column"><Field label="Email address"><input type="email" value={contact.email} onChange={e => setContact({...contact, email: e.target.value})} /></Field><Field label="Mobile number"><span className="prefix">+91</span><input value={contact.mobile} onChange={e => setContact({...contact, mobile: e.target.value.replace(/\D/g, "").slice(0,10)})} /></Field></div></div>
          {error && <p className="checkout-error">{error}</p>}<button className="primary-button checkout-next">Continue to payment<Icon name="arrow" size={18} /></button>
        </form> : <form onSubmit={pay}>
          <div className="section-heading"><div><span className="eyebrow">SECURE PAYMENT</span><h1>Complete your booking</h1><p>Your payment information is encrypted and secure.</p></div></div>
          <div className="payment-tabs"><button type="button" className="active"><Icon name="card" />Credit / Debit card</button><button type="button">UPI</button><button type="button">Net banking</button></div>
          <div className="form-card payment-card">
            <div className="secure-badge"><Icon name="shield" size={17} />256-bit secure payment</div>
            <Field label="Card number" icon="card"><input value={payment.card} onChange={e => setPayment({...payment, card: e.target.value.replace(/\D/g,"").replace(/(.{4})/g,"$1 ").trim().slice(0,19)})} placeholder="1234 5678 9012 3456" /></Field>
            <div className="two-column"><Field label="Expiry date"><input value={payment.expiry} onChange={e => setPayment({...payment, expiry: e.target.value.replace(/\D/g,"").replace(/^(\d{2})(\d)/,"$1/$2").slice(0,5)})} placeholder="MM/YY" /></Field><Field label="CVV"><input type="password" value={payment.cvv} onChange={e => setPayment({...payment, cvv: e.target.value.replace(/\D/g,"").slice(0,3)})} placeholder="•••" /></Field></div>
            <Field label="Name on card" icon="user"><input value={payment.name} onChange={e => setPayment({...payment, name: e.target.value})} /></Field>
          </div>
          {error && <p className="checkout-error">{error}</p>}<button className="primary-button checkout-next">Pay ₹{total.toLocaleString("en-IN")} securely<Icon name="shield" size={18} /></button>
        </form>}
      </section>
      <aside className="fare-card"><h3>Fare summary</h3><div className="mini-route"><b>{search.from}</b><Icon name="arrow" size={17} /><b>{search.to}</b></div><p>{bus.operator} · {bus.departure}</p><div className="fare-lines"><span><small>Seats</small><b>{seats.join(", ")}</b></span><span><small>Base fare</small><b>₹{base.toLocaleString("en-IN")}</b></span><span><small>Booking fee & taxes</small><b>₹{fee.toLocaleString("en-IN")}</b></span></div><div className="total-row"><span>Total</span><strong>₹{total.toLocaleString("en-IN")}</strong></div><div className="fare-assurance"><Icon name="check" size={16} />Free cancellation within 30 minutes</div></aside>
    </div>
  </main>;
}

function Confirmation({ booking, onBookings, onHome }: { booking: Booking; onBookings: () => void; onHome: () => void }) {
  return <main className="confirmation-page"><div className="confetti c1" /><div className="confetti c2" /><div className="confetti c3" />
    <div className="success-icon"><Icon name="check" size={36} /></div><span className="eyebrow">BOOKING CONFIRMED</span><h1>You’re all set to roam.</h1><p>Your ticket has been booked and a confirmation was sent to your email.</p>
    <section className="ticket-card"><div className="ticket-top"><div><span>BOOKING ID</span><b>{booking.id}</b></div><span className="confirmed-pill"><Icon name="check" size={14} />Confirmed</span></div><div className="ticket-main"><div className="ticket-operator"><div className={`operator-logo logo-${booking.bus.id}`}>{booking.bus.operator.slice(0,2)}</div><div><h3>{booking.bus.operator}</h3><p>{booking.bus.type}</p></div></div><div className="ticket-route"><div><strong>{booking.bus.departure}</strong><span>{booking.search.from}</span><small>{booking.bus.boarding}</small></div><div className="ticket-line"><Icon name="bus" size={18} /><span>{booking.bus.duration}</span></div><div><strong>{booking.bus.arrival}</strong><span>{booking.search.to}</span><small>{booking.bus.dropping}</small></div></div><div className="ticket-meta"><div><span>Journey date</span><b>{new Date(`${booking.search.journeyDate}T12:00:00`).toLocaleDateString("en-IN", { day: "numeric", month: "long", year: "numeric" })}</b></div><div><span>Seats</span><b>{booking.seats.join(", ")}</b></div><div><span>Passengers</span><b>{booking.passengerNames.join(", ")}</b></div><div><span>Amount paid</span><b>₹{booking.total.toLocaleString("en-IN")}</b></div></div></div><div className="ticket-bottom"><Icon name="shield" size={17} />Carry a valid photo ID for verification at boarding.</div></section>
    <div className="confirmation-actions"><button className="primary-button" onClick={onBookings}>View my bookings</button><button className="secondary-button" onClick={onHome}>Book another trip</button></div>
  </main>;
}

function Bookings({ bookings, setBookings, onHome }: { bookings: Booking[]; setBookings: (b: Booking[]) => void; onHome: () => void }) {
  const cancel = (id: string) => {
    const updated = bookings.map(item => item.id === id ? {...item, status: "Cancelled" as const} : item);
    setBookings(updated); localStorage.setItem("roambus_bookings", JSON.stringify(updated));
  };
  return <main className="bookings-page"><div className="page-title"><span className="eyebrow">YOUR JOURNEYS</span><h1>My bookings</h1><p>Everything you need for every trip, all in one place.</p></div>
    {bookings.length === 0 ? <div className="empty-state"><span><Icon name="ticket" size={34} /></span><h2>No trips booked yet</h2><p>Your future journeys will appear here once you make a booking.</p><button className="primary-button" onClick={onHome}>Find a bus</button></div> :
      <div className="booking-list">{bookings.map(booking => <article className="booking-item" key={booking.id}><div className="booking-date"><span>{new Date(`${booking.search.journeyDate}T12:00:00`).toLocaleDateString("en-IN",{month:"short"}).toUpperCase()}</span><b>{new Date(`${booking.search.journeyDate}T12:00:00`).getDate()}</b></div><div className="booking-info"><div><span className={`status ${booking.status.toLowerCase()}`}>{booking.status}</span><small>{booking.id}</small></div><h3>{booking.search.from} <Icon name="arrow" size={18} /> {booking.search.to}</h3><p>{booking.bus.operator} · {booking.bus.departure} · Seats {booking.seats.join(", ")}</p></div><div className="booking-price"><span>Amount paid</span><b>₹{booking.total.toLocaleString("en-IN")}</b>{booking.status === "Confirmed" && <button onClick={() => cancel(booking.id)}>Cancel booking</button>}</div></article>)}</div>}
  </main>;
}

export default function App() {
  const [view, setView] = useState<View>(() => localStorage.getItem("roambus_session") ? "home" : "login");
  const [user, setUser] = useState<User | null>(() => JSON.parse(localStorage.getItem("roambus_session") || "null"));
  const [search, setSearch] = useState<Search>({ from: "Chennai", to: "Bengaluru", journeyDate: futureDate, returnDate: "", passengers: 2 });
  const [selectedBus, setSelectedBus] = useState<Bus | null>(null);
  const [selectedSeats, setSelectedSeats] = useState<string[]>([]);
  const [bookings, setBookings] = useState<Booking[]>(() => JSON.parse(localStorage.getItem("roambus_bookings") || "[]"));
  const [latestBooking, setLatestBooking] = useState<Booking | null>(null);

  useEffect(() => {
    const existing: User[] = JSON.parse(localStorage.getItem("roambus_users") || "[]");
    if (!existing.some(item => item.email === "demo@roambus.in")) {
      localStorage.setItem("roambus_users", JSON.stringify([...existing, { name: "Demo Traveller", email: "demo@roambus.in", mobile: "9876543210", password: "demo123" }]));
    }
  }, []);

  const authenticate = (account: User) => { localStorage.setItem("roambus_session", JSON.stringify(account)); setUser(account); setView("home"); };
  const logout = () => { localStorage.removeItem("roambus_session"); setUser(null); setView("login"); };
  const completeBooking = (booking: Booking) => { const updated = [booking, ...bookings]; setBookings(updated); localStorage.setItem("roambus_bookings", JSON.stringify(updated)); setLatestBooking(booking); setView("confirmation"); };

  if (!user || view === "login" || view === "register" || view === "forgot") return <AuthShell mode={view === "register" ? "register" : view === "forgot" ? "forgot" : "login"} setView={setView} onAuth={authenticate} />;
  return <div className="app-shell">
    {!["confirmation"].includes(view) && <AppHeader view={view} setView={setView} user={user} logout={logout} />}
    {view === "home" && <Home user={user} search={search} onSearch={value => { setSearch(value); setView("results"); }} />}
    {view === "results" && <Results search={search} onModify={() => setView("home")} onSelect={bus => { setSelectedBus(bus); setView("seats"); }} />}
    {view === "seats" && selectedBus && <SeatSelection bus={selectedBus} search={search} onBack={() => setView("results")} onContinue={seats => { setSelectedSeats(seats); setView("checkout"); }} />}
    {view === "checkout" && selectedBus && <Checkout bus={selectedBus} search={search} seats={selectedSeats} user={user} onBack={() => setView("seats")} onComplete={completeBooking} />}
    {view === "confirmation" && latestBooking && <Confirmation booking={latestBooking} onBookings={() => setView("bookings")} onHome={() => setView("home")} />}
    {view === "bookings" && <Bookings bookings={bookings} setBookings={setBookings} onHome={() => setView("home")} />}
  </div>;
}
