import React, { useState, useEffect } from "react";
import axios from "axios";
import { Toaster, toast } from "react-hot-toast";
import "bootstrap/dist/css/bootstrap.min.css";
import "bootstrap-icons/font/bootstrap-icons.css";

// Add custom fonts
const fontStyles = `
  @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;500;600;700&family=Inter:wght@400;500;600&display=swap');
  
  body {
    font-family: 'Inter', sans-serif;
  }
  
  h1, h2, h3, h4, h5, h6 {
    font-family: 'Poppins', sans-serif;
  }
`;

function App() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    document.title = "Job Radar Dashboard";
  }, []);

  const startJobScheduler = async () => {
    if (!email) {
      toast.error("Please enter your email.");
      return;
    }

    setLoading(true);

    try {
      const response = await axios.post("http://localhost:5000/main", {
        email: email,
      });
      toast.success(response.data.message || "Job scheduler started successfully!");
    } catch (error) {
      toast.error("Error starting job scheduler.");
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="container-fluid d-flex flex-column justify-content-center align-items-center min-vh-100"
      style={{ 
        background: "linear-gradient(135deg, #6a11cb 0%, #2575fc 100%)",
        position: "relative",
        overflow: "hidden",
        padding: "2rem 0"
      }}
    >
      <style>{fontStyles}</style>
      <div className="position-absolute top-0 start-0 w-100 h-100" style={{ 
        background: "url('data:image/svg+xml,%3Csvg width=\"20\" height=\"20\" viewBox=\"0 0 20 20\" xmlns=\"http://www.w3.org/2000/svg\"%3E%3Cg fill=\"%23ffffff\" fill-opacity=\"0.05\" fill-rule=\"evenodd\"%3E%3Ccircle cx=\"2\" cy=\"2\" r=\"1\"/%3E%3C/g%3E%3C/svg%3E')",
        opacity: 0.1
      }}></div>
      
      <Toaster position="top-center" reverseOrder={false} />
      <div
        className="card shadow-lg p-5 border-0 rounded-4 position-relative overflow-hidden"
        style={{ 
          maxWidth: "550px", 
          width: "100%", 
          background: "rgba(255, 255, 255, 0.95)",
          backdropFilter: "blur(10px)",
          border: "1px solid rgba(255, 255, 255, 0.2)",
          margin: "2rem auto"
        }}
      >
        <div className="ribbon bg-danger text-white p-2 position-absolute top-0 start-0 fs-6" 
          style={{ 
            transform: "rotate(-20deg)", 
            left: "-30px", 
            top: "15px",
            boxShadow: "0 2px 4px rgba(0,0,0,0.2)",
            fontFamily: "'Poppins', sans-serif",
            fontWeight: "600",
            letterSpacing: "0.5px"
          }}>
          🔥 Trending
        </div>
        <div className="card-body text-center">
          <div className="logo-container mb-2" style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            padding: "0 10px"
          }}>
            <div className="logo-icon" style={{
              width: "70px",
              height: "70px",
              background: "linear-gradient(45deg, #6a11cb, #2575fc)",
              borderRadius: "16px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              boxShadow: "0 4px 15px rgba(106, 17, 203, 0.3)",
              animation: "pulse 2s infinite"
            }}>
              <i className="bi bi-briefcase-fill" style={{
                fontSize: "32px",
                color: "white"
              }}></i>
            </div>
          </div>
          <h1 className="display-5 fw-bold text-primary mb-3" style={{ 
            background: "linear-gradient(45deg, #6a11cb, #2575fc)",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: "12px",
            fontFamily: "'Poppins', sans-serif",
            letterSpacing: "-0.02em",
            fontSize: "2.5rem",
            lineHeight: "1.2",
            margin: "0 auto",
            width: "100%",
            padding: "0 15px",
            flexWrap: "wrap"
          }}>
            <span style={{
              display: "inline-block",
              whiteSpace: "normal",
              wordBreak: "normal"
            }}>Job Radar Dashboard</span>
            <span style={{ 
              fontSize: "1.2em",
              display: "inline-block",
              animation: "rocket 2s infinite",
              WebkitTextFillColor: "initial",
              marginLeft: "5px"
            }}>🚀</span>
          </h1>
          <p className="text-muted mb-4" style={{ 
            fontSize: "1.15rem",
            fontFamily: "'Inter', sans-serif",
            fontWeight: "500",
            lineHeight: "1.6",
            maxWidth: "400px",
            margin: "0 auto"
          }}>
            Stay ahead with real-time job alerts and never miss an opportunity!
          </p>
          <div className="mb-4">
            <input
              type="email"
              placeholder="Enter your email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="form-control text-center border-2 border-primary shadow-lg p-3 rounded-3"
              style={{ 
                transition: "all 0.3s ease",
                borderColor: "#6a11cb",
                fontFamily: "'Inter', sans-serif",
                fontSize: "1.1rem",
                fontWeight: "500",
                maxWidth: "350px",
                margin: "0 auto"
              }}
            />
          </div>
          <button
            onClick={startJobScheduler}
            disabled={loading}
            className="btn btn-gradient w-100 fw-bold shadow-lg text-white p-3 rounded-3 position-relative overflow-hidden"
            style={{ 
              background: "linear-gradient(45deg, #ff416c, #ff4b2b)",
              border: "none",
              transition: "all 0.3s ease",
              transform: "translateY(0)",
              boxShadow: "0 4px 15px rgba(255, 65, 108, 0.3)",
              fontFamily: "'Poppins', sans-serif",
              fontSize: "1.15rem",
              letterSpacing: "0.5px",
              maxWidth: "350px",
              margin: "0 auto"
            }}
            onMouseOver={(e) => e.currentTarget.style.transform = "translateY(-2px)"}
            onMouseOut={(e) => e.currentTarget.style.transform = "translateY(0)"}
          >
            <i className="bi bi-lightning-charge-fill me-2"></i>
            {loading ? "Starting..." : "Start Job Scheduler"}
          </button>
          <p className="text-muted mt-4" style={{ 
            fontSize: "0.95rem",
            fontFamily: "'Inter', sans-serif",
            fontWeight: "500",
            maxWidth: "300px",
            margin: "0 auto"
          }}>
            🔔 Get instant job alerts straight to your inbox!
          </p>
        </div>
      </div>

      <style>
        {`
          @keyframes rocket {
            0% { transform: translateY(0); }
            50% { transform: translateY(-5px); }
            100% { transform: translateY(0); }
          }
          
          @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.05); }
            100% { transform: scale(1); }
          }
        `}
      </style>

      <div className="text-white text-center position-absolute bottom-0 w-100 py-3" 
        style={{ 
          background: "rgba(0, 0, 0, 0.1)",
          backdropFilter: "blur(5px)",
          fontFamily: "'Inter', sans-serif",
          fontSize: "0.9rem",
          fontWeight: "500",
          marginTop: "2rem"
        }}>
        <p className="mb-0">
          © {new Date().getFullYear()} Job Radar. All rights reserved.
        </p>
      </div>
    </div>
  );
}

export default App;
