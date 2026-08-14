import { useState, useRef, useEffect, useCallback } from 'react';
import { X, Download, ShieldCheck, Copy, Check } from 'lucide-react';
import './CertificateModal.css';

const TIER_COLORS = {
  bronze: { primary: '#CD7F32', light: '#E8A86C', glow: 'rgba(205, 127, 50, 0.4)' },
  silver: { primary: '#CBD5E1', light: '#FFFFFF', glow: 'rgba(203, 213, 225, 0.4)' },
  gold: { primary: '#F59E0B', light: '#FDE68A', glow: 'rgba(245, 158, 11, 0.45)' },
  platinum: { primary: '#38BDF8', light: '#E0F2FE', glow: 'rgba(56, 189, 248, 0.45)' },
  diamond: { primary: '#A78BFA', light: '#EDE9FE', glow: 'rgba(167, 139, 250, 0.5)' }
};

export default function CertificateModal({
  credential,
  user,
  onClose
}) {
  const [aspectRatio, setAspectRatio] = useState('16:9'); // '16:9' | '1:1' | '9:16'
  const [copied, setCopied] = useState(false);
  const canvasRef = useRef(null);

  const recipientName = user?.full_name || user?.username || 'Mastery Practitioner';
  const mkcId = user?.mkc_id || (user?.id ? `MKC-${user.id}` : 'MKC-VERIFIED');
  const tierKey = (credential?.tier || 'bronze').toLowerCase();
  const tierConfig = TIER_COLORS[tierKey] || TIER_COLORS.bronze;

  const renderCertificate = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas || !credential) return;

    let width = 1200;
    let height = 675;

    if (aspectRatio === '1:1') {
      width = 1080;
      height = 1080;
    } else if (aspectRatio === '9:16') {
      width = 1080;
      height = 1920;
    }

    canvas.width = width;
    canvas.height = height;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // 1. Deep Space Background
    const bgGrad = ctx.createRadialGradient(width / 2, height / 2, 50, width / 2, height / 2, width * 0.8);
    bgGrad.addColorStop(0, '#0F1A2E');
    bgGrad.addColorStop(0.6, '#080E18');
    bgGrad.addColorStop(1, '#04070D');
    ctx.fillStyle = bgGrad;
    ctx.fillRect(0, 0, width, height);

    // 2. Subtle Geometric Security Grid
    ctx.strokeStyle = 'rgba(56, 189, 248, 0.04)';
    ctx.lineWidth = 1;
    const gridSize = 40;
    for (let x = 0; x < width; x += gridSize) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, height);
      ctx.stroke();
    }
    for (let y = 0; y < height; y += gridSize) {
      ctx.beginPath();
      ctx.moveTo(0, y);
      ctx.lineTo(width, y);
      ctx.stroke();
    }

    // 3. Central Ambient Glow
    const centerGlow = ctx.createRadialGradient(width / 2, height * 0.45, 10, width / 2, height * 0.45, width * 0.45);
    centerGlow.addColorStop(0, tierConfig.glow);
    centerGlow.addColorStop(1, 'transparent');
    ctx.fillStyle = centerGlow;
    ctx.fillRect(0, 0, width, height);

    // 4. Double Border Frame
    const margin = aspectRatio === '9:16' ? 50 : 35;
    
    // Outer Frame
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.12)';
    ctx.lineWidth = 2;
    ctx.strokeRect(margin, margin, width - margin * 2, height - margin * 2);

    // Inner Gold/Tier Border
    ctx.strokeStyle = tierConfig.primary;
    ctx.lineWidth = 1.5;
    const innerMargin = margin + 12;
    ctx.strokeRect(innerMargin, innerMargin, width - innerMargin * 2, height - innerMargin * 2);

    // Corner Ornaments
    const corners = [
      [innerMargin, innerMargin],
      [width - innerMargin, innerMargin],
      [innerMargin, height - innerMargin],
      [width - innerMargin, height - innerMargin]
    ];
    ctx.fillStyle = tierConfig.primary;
    corners.forEach(([cx, cy]) => {
      ctx.beginPath();
      ctx.arc(cx, cy, 4, 0, Math.PI * 2);
      ctx.fill();
    });

    // 5. Header Branding
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';

    let curY = aspectRatio === '9:16' ? 160 : (aspectRatio === '1:1' ? 120 : 90);

    ctx.font = '700 13px system-ui, -apple-system, sans-serif';
    ctx.fillStyle = '#38BDF8';
    ctx.letterSpacing = '4px';
    ctx.fillText('MASTERY KEY COACH • OFFICIAL CREDENTIAL', width / 2, curY);

    curY += aspectRatio === '9:16' ? 45 : 30;
    ctx.font = '800 11px system-ui, -apple-system, sans-serif';
    ctx.fillStyle = tierConfig.primary;
    ctx.letterSpacing = '3px';
    ctx.fillText(`${tierKey.toUpperCase()} LEVEL ACHIEVEMENT`, width / 2, curY);

    // 6. Presentation Line
    curY += aspectRatio === '9:16' ? 100 : (aspectRatio === '1:1' ? 70 : 50);
    ctx.font = '400 14px Georgia, serif';
    ctx.fillStyle = 'rgba(255, 255, 255, 0.6)';
    ctx.letterSpacing = '1px';
    ctx.fillText('THIS IS SERVER-AUTHORITATIVELY CERTIFIED TO', width / 2, curY);

    // 7. Recipient Name
    curY += aspectRatio === '9:16' ? 80 : (aspectRatio === '1:1' ? 65 : 48);
    ctx.font = `800 ${aspectRatio === '9:16' ? '44px' : '36px'} Georgia, serif`;
    const nameGrad = ctx.createLinearGradient(width / 2 - 200, curY, width / 2 + 200, curY);
    nameGrad.addColorStop(0, '#FFFFFF');
    nameGrad.addColorStop(0.5, tierConfig.light);
    nameGrad.addColorStop(1, '#FFFFFF');
    ctx.fillStyle = nameGrad;
    ctx.letterSpacing = '0.5px';
    ctx.fillText(recipientName, width / 2, curY);

    // Identifier tag
    curY += aspectRatio === '9:16' ? 40 : 30;
    ctx.font = '600 13px monospace';
    ctx.fillStyle = '#38BDF8';
    ctx.fillText(`[ ${mkcId} ]`, width / 2, curY);

    // Divider Line
    curY += aspectRatio === '9:16' ? 70 : (aspectRatio === '1:1' ? 50 : 35);
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.15)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(width / 2 - 120, curY);
    ctx.lineTo(width / 2 + 120, curY);
    ctx.stroke();

    // 8. Achievement Title
    curY += aspectRatio === '9:16' ? 80 : (aspectRatio === '1:1' ? 65 : 45);
    ctx.font = `800 ${aspectRatio === '9:16' ? '38px' : '30px'} system-ui, -apple-system, sans-serif`;
    ctx.fillStyle = '#FFFFFF';
    ctx.fillText(credential.title, width / 2, curY);

    // 9. Achievement Description
    curY += aspectRatio === '9:16' ? 55 : 35;
    ctx.font = '400 15px system-ui, -apple-system, sans-serif';
    ctx.fillStyle = 'rgba(255, 255, 255, 0.75)';
    ctx.letterSpacing = '0.2px';
    
    // Wrap description if too wide
    const maxWidth = width - (margin * 2 + 80);
    const words = (credential.description || '').split(' ');
    let line = '';
    const lines = [];
    words.forEach(w => {
      const testLine = line + w + ' ';
      if (ctx.measureText(testLine).width > maxWidth && line !== '') {
        lines.push(line);
        line = w + ' ';
      } else {
        line = testLine;
      }
    });
    lines.push(line);

    lines.forEach(l => {
      ctx.fillText(l.trim(), width / 2, curY);
      curY += 24;
    });

    // 10. Seal & Verification Footer
    const footerY = height - (aspectRatio === '9:16' ? 180 : (aspectRatio === '1:1' ? 140 : 100));

    // Security Shield Seal
    ctx.fillStyle = 'rgba(16, 185, 129, 0.15)';
    ctx.strokeStyle = '#10B981';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(width / 2, footerY - 20, 26, 0, Math.PI * 2);
    ctx.fill();
    ctx.stroke();

    ctx.font = '800 10px system-ui, -apple-system, sans-serif';
    ctx.fillStyle = '#10B981';
    ctx.letterSpacing = '1px';
    ctx.fillText('VERIFIED', width / 2, footerY - 20);

    const issueDate = credential.issued_at
      ? new Date(credential.issued_at).toLocaleDateString('en-US', {
          month: 'long',
          day: 'numeric',
          year: 'numeric'
        })
      : 'Authoritatively Issued';

    ctx.font = '500 12px system-ui, -apple-system, sans-serif';
    ctx.fillStyle = 'rgba(255, 255, 255, 0.5)';
    ctx.letterSpacing = '0.5px';
    ctx.fillText(`Issued on ${issueDate} • +${credential.xp_value || 50} Mastery XP Awarded`, width / 2, footerY + 25);

    ctx.font = '400 10px monospace';
    ctx.fillStyle = 'rgba(255, 255, 255, 0.3)';
    ctx.fillText(`HASH: MKC-AUTH-${(credential.slug || 'CRED').toUpperCase()}-${credential.id || 101}`, width / 2, footerY + 45);

  }, [aspectRatio, credential, mkcId, recipientName, tierConfig, tierKey]);

  useEffect(() => {
    renderCertificate();
  }, [renderCertificate]);

  const handleDownload = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const link = document.createElement('a');
    const slug = (credential?.slug || 'credential').toLowerCase();
    link.download = `MKC_Certificate_${slug}_${aspectRatio.replace(':', 'x')}.png`;
    link.href = canvas.toDataURL('image/png', 1.0);
    link.click();
  };

  const handleCopyLink = () => {
    navigator.clipboard.writeText(window.location.href);
    setCopied(true);
    setTimeout(() => setCopied(false), 2500);
  };

  return (
    <div className="cert-modal-backdrop" onClick={onClose}>
      <div 
        className="cert-modal-card glass-panel" 
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
      >
        <div className="cert-modal-header">
          <div className="cert-header-title">
            <ShieldCheck size={20} style={{ color: tierConfig.primary }} />
            <div>
              <h3>Official Mastery Credential</h3>
              <span className="cert-header-sub">Server-verified proof of discipline & execution</span>
            </div>
          </div>
          <button onClick={onClose} className="cert-close-btn" aria-label="Close certificate">
            <X size={18} />
          </button>
        </div>

        <div className="cert-aspect-selector">
          <span className="aspect-label">Export Format:</span>
          <button 
            className={`aspect-btn ${aspectRatio === '16:9' ? 'active' : ''}`}
            onClick={() => setAspectRatio('16:9')}
          >
            16:9 (LinkedIn / X)
          </button>
          <button 
            className={`aspect-btn ${aspectRatio === '1:1' ? 'active' : ''}`}
            onClick={() => setAspectRatio('1:1')}
          >
            1:1 (Post / Square)
          </button>
          <button 
            className={`aspect-btn ${aspectRatio === '9:16' ? 'active' : ''}`}
            onClick={() => setAspectRatio('9:16')}
          >
            9:16 (Story / Reels)
          </button>
        </div>

        <div className="cert-canvas-container">
          <canvas ref={canvasRef} className={`cert-canvas aspect-${aspectRatio.replace(':', '-')}`} />
        </div>

        <div className="cert-modal-footer">
          <button onClick={handleCopyLink} className="cert-btn btn-secondary">
            {copied ? <Check size={16} /> : <Copy size={16} />}
            <span>{copied ? 'Link Copied!' : 'Share Link'}</span>
          </button>
          <button onClick={handleDownload} className="cert-btn btn-primary">
            <Download size={16} />
            <span>Download Certificate (PNG)</span>
          </button>
        </div>
      </div>
    </div>
  );
}
