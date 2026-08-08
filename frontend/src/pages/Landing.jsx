import Navbar from "../components/Navbar";
import Hero from "../components/Hero";
import WhySection from "../components/WhySection";
import MasteryLoop from "../components/MasteryLoop";
import Features from "../components/Features";
import Footer from "../components/Footer";

function Landing() {
  return (
    <>
      <Navbar />
      <Hero />
      <WhySection />
      <MasteryLoop />
      <Features />
      <Footer />
    </>
  );
}

export default Landing;