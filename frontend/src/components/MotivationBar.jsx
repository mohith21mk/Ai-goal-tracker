import './MotivationBar.css';

const motivationItems = [
  {
    id: 1,
    label: "Daily Reminder",
    quote: "You're becoming the person your future needs.",
    color: "#38BDF8"
  },
  {
    id: 2,
    label: "Grateful For The Journey",
    quote: "Turn obstacles into fuel for your legacy.",
    color: "#FBBF24"
  },
  {
    id: 3,
    label: "Focused On A Better Tomorrow",
    quote: "Consistency compounds into extraordinary results.",
    color: "#3B82F6"
  },
  {
    id: 4,
    label: "Built For Freedom & Legacy",
    quote: "Master yourself, master your universe.",
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
          </div>
        </div>
      ))}
    </div>
  );
};

export default MotivationBar;
