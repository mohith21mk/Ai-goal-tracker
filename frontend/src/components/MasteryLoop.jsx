import "./MasteryLoop.css";

function MasteryLoop() {
  return (
    <section className="mastery-loop">

      <h2>The Mastery Loop</h2>

      <p className="loop-subtitle">
        Discipline isn't built overnight.
        It's created through small actions repeated every day.
      </p>

      <div className="loop-container">

        <div className="loop-card">
          🎯
          <h3>1. Set Your Goal</h3>
          <p>
            Define one meaningful goal you want to achieve.
          </p>
        </div>

        <div className="arrow">↓</div>

        <div className="loop-card">
          🤖
          <h3>2. AI Creates Daily Missions</h3>
          <p>
            Your AI coach breaks the goal into simple daily tasks.
          </p>
        </div>

        <div className="arrow">↓</div>

        <div className="loop-card">
          ✅
          <h3>3. Complete Today's Mission</h3>
          <p>
            Small consistent actions build momentum.
          </p>
        </div>

        <div className="arrow">↓</div>

        <div className="loop-card">
          📈
          <h3>4. Track Progress</h3>
          <p>
            Every completed mission increases your consistency score.
          </p>
        </div>

        <div className="arrow">↓</div>

        <div className="loop-card">
          🏆
          <h3>5. Build Discipline</h3>
          <p>
            Daily consistency becomes long-term discipline.
          </p>
        </div>

      </div>

    </section>
  );
}

export default MasteryLoop;