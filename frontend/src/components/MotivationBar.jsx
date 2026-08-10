import './MotivationBar.css';

const motivationItems = [
  {
    id: 1,
    label: "Daily Identity",
    quote: "You're becoming the person your future needs.",
    author: "Mastery Key Protocol",
    color: "#A78BFA"
  },
  {
    id: 2,
    label: "Stoic Fortitude",
    quote: "Turn obstacles into fuel for your legacy.",
    author: "Marcus Aurelius",
    color: "#38BDF8"
  },
  {
    id: 3,
    label: "Relentless Discipline",
    quote: "Consistency compounds into extraordinary results.",
    author: "Mastery Key Philosophy",
    color: "#3B82F6"
  },
  {
    id: 4,
    label: "Legacy Vision",
    quote: "Master yourself, master your universe.",
    author: "Epictetus",
    color: "#10B981"
  }
];

const MotivationBar = () => {
  return (
    <div className="motivation-bar-container">
      {motivationItems.map((item) => (
        <div key={item.id} className="motivation-pill glass-panel">
          <div className="motivation-pill-accent" style={{ background: item.color }} />
          <div className="motivation-pill-content">
            <span className="motivation-label font-display" style={{ color: item.color }}>
              {item.label}
            </span>
            <p className="motivation-quote">"{item.quote}"</p>
            <span className="motivation-author">— {item.author}</span>
          </div>
        </div>
      ))}
    </div>
  );
};

export default MotivationBar;
