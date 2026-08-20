import { useState, useRef, useEffect, useCallback } from 'react';
import { X, Download, ShieldCheck, Copy, Check, Award, AlertTriangle } from 'lucide-react';
import { MKC_LOGO_SVG_STRING } from './MKCLogo';
import './CertificateModal.css';

const TIER_COLORS = {
  bronze: {
    name: 'BRONZE',
    primary: '#CD7F32',
    light: '#F5C29A',
    dark: '#784212',
    glow: 'rgba(205, 127, 50, 0.45)',
    borderGrad: ['#F5C29A', '#CD7F32', '#8C4B18', '#F5C29A']
  },
  silver: {
    name: 'SILVER',
    primary: '#94A3B8',
    light: '#E2E8F0',
    dark: '#334155',
    glow: 'rgba(148, 163, 184, 0.45)',
    borderGrad: ['#F8FAFC', '#94A3B8', '#475569', '#E2E8F0']
  },
  gold: {
    name: 'GOLD',
    primary: '#F59E0B',
    light: '#FDE68A',
    dark: '#78350F',
    glow: 'rgba(245, 158, 11, 0.55)',
    borderGrad: ['#FEF3C7', '#F59E0B', '#92400E', '#FBBF24']
  },
  platinum: {
    name: 'PLATINUM',
    primary: '#38BDF8',
    light: '#BAE6FD',
    dark: '#0369A1',
    glow: 'rgba(56, 189, 248, 0.65)',
    borderGrad: ['#E0F2FE', '#38BDF8', '#0284C7', '#7DD3FC']
  },
  diamond: {
    name: 'DIAMOND',
    primary: '#A855F7',
    light: '#E9D5FF',
    dark: '#581C87',
    glow: 'rgba(168, 85, 247, 0.65)',
    borderGrad: ['#F3E8FF', '#A855F7', '#6B21A8', '#C084FC']
  },
  obsidian: {
    name: 'OBSIDIAN',
    primary: '#10B981',
    light: '#A7F3D0',
    dark: '#064E3B',
    glow: 'rgba(16, 185, 129, 0.65)',
    borderGrad: ['#D1FAE5', '#10B981', '#047857', '#34D399']
  },
  default: {
    name: 'MASTER',
    primary: '#38BDF8',
    light: '#BAE6FD',
    dark: '#0369A1',
    glow: 'rgba(56, 189, 248, 0.55)',
    borderGrad: ['#E0F2FE', '#38BDF8', '#0284C7', '#7DD3FC']
  }
};

const MOTIVATIONAL_QUOTES = {
  streak_badge: '“Discipline today. Freedom tomorrow. Legacy forever.”',
  mission_badge: '“The standard is excellence. Execution is everything.”',
  blueprint_badge: '“Vision without execution is hallucination. Strategy realized.”',
  mastery_badge: '“Mastery is not an outcome. It is a lifelong sovereign pursuit.”',
  default: '“Discipline today. Freedom tomorrow. Legacy forever.”'
};

/**
 * Safely sets canvas letter-spacing if supported by the browser engine
 */
function setCanvasLetterSpacing(ctx, spacing) {
  try {
    if (ctx && 'letterSpacing' in ctx) {
      ctx.letterSpacing = spacing;
    }
  } catch {
    // Ignore unsupported browser property
  }
}

/**
 * Text wrapping and multi-line rendering helper for Canvas
 */
function wrapAndRenderText(ctx, text, x, y, maxWidth, lineHeight, align = 'center') {
  if (!text && text !== 0) return y;
  const str = String(text).trim();
  if (!str) return y;

  const words = str.split(' ');
  let line = '';
  let curY = y;

  ctx.textAlign = align;

  for (let n = 0; n < words.length; n++) {
    const testLine = line + words[n] + ' ';
    const metrics = ctx.measureText(testLine);
    if (metrics.width > maxWidth && n > 0) {
      ctx.fillText(line.trim(), x, curY);
      line = words[n] + ' ';
      curY += lineHeight;
    } else {
      line = testLine;
    }
  }
  if (line.trim()) {
    ctx.fillText(line.trim(), x, curY);
    curY += lineHeight;
  }
  return curY;
}

export default function CertificateModal({
  credential,
  user,
  onClose
}) {
  const [aspectRatio, setAspectRatio] = useState('16:9'); // '16:9' | '1:1' | '9:16'
  const [copied, setCopied] = useState(false);
  const [logoLoaded, setLogoLoaded] = useState(false);
  const canvasRef = useRef(null);
  const heroLogoImgRef = useRef(null);

  // 1. Safe Normalized Credential Model
  const safeCredential = {
    id: credential?.id ?? null,
    title: (credential?.title || 'Mastery Vanguard Achievement').trim(),
    description: (credential?.description || 'Demonstrated consistent focus, discipline, and execution across personal milestones.').trim(),
    slug: (credential?.slug || 'mastery-achievement').trim(),
    tier: (credential?.tier || 'gold').toLowerCase().replace(' tier', '').trim(),
    xpValue: Number(credential?.xp_value ?? credential?.xpValue ?? credential?.xp_awarded ?? 150) || 150,
    issuedAt: credential?.issued_at || credential?.issuedAt || null,
    credentialType: credential?.credential_type || credential?.credentialType || 'default'
  };

  // 2. Safe Normalized User Model
  const safeUser = {
    fullName: (user?.full_name || user?.fullName || user?.username || 'Mastery Practitioner').trim(),
    username: user?.username ? `@${user.username.replace('@', '')}` : '',
    mkcId: user?.mkc_id || user?.mkcId || (user?.id ? `MKC-${user.id}` : 'MKC-VERIFIED')
  };

  const tierKey = safeCredential.tier in TIER_COLORS ? safeCredential.tier : 'gold';
  const tierConfig = TIER_COLORS[tierKey] || TIER_COLORS.gold;

  const quote = MOTIVATIONAL_QUOTES[safeCredential.credentialType] || MOTIVATIONAL_QUOTES.default;

  let issueDateFormatted = 'Verified Milestone';
  try {
    if (safeCredential.issuedAt) {
      const d = new Date(safeCredential.issuedAt);
      if (!isNaN(d.getTime())) {
        issueDateFormatted = d.toLocaleDateString('en-US', {
          month: 'long',
          day: 'numeric',
          year: 'numeric'
        });
      }
    } else {
      issueDateFormatted = new Date().toLocaleDateString('en-US', {
        month: 'long',
        day: 'numeric',
        year: 'numeric'
      });
    }
  } catch {
    issueDateFormatted = new Date().toLocaleDateString('en-US', {
      month: 'long',
      day: 'numeric',
      year: 'numeric'
    });
  }

  const credHash = `MKC-AUTH-${safeCredential.slug.toUpperCase()}-${safeCredential.id || 101}`;
  const idTag = safeUser.username ? `[ MKC VERIFIED ✓ • ${safeUser.username} ]` : `[ MKC VERIFIED ✓ • ${safeUser.mkcId} ]`;

  // Preload the EXACT MKC Hero Visual SVG from MKCLogo.jsx
  useEffect(() => {
    let active = true;
    try {
      const blob = new Blob([MKC_LOGO_SVG_STRING], { type: 'image/svg+xml;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const img = new Image();
      img.crossOrigin = 'anonymous';
      img.src = url;
      img.onload = () => {
        if (active) {
          heroLogoImgRef.current = img;
          setLogoLoaded(true);
        }
      };
      return () => {
        active = false;
        URL.revokeObjectURL(url);
      };
    } catch (err) {
      console.warn('Failed to preload SVG hero visual for canvas:', err);
    }
  }, []);

  // Keyboard accessibility
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') onClose();
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [onClose]);

  // Master Canvas Render Function with Dedicated Per-Aspect-Ratio Composition
  const renderCertificate = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas || !credential) return;

    try {
      let width = 2400;
      let height = 1350;

      if (aspectRatio === '1:1') {
        width = 1800;
        height = 1800;
      } else if (aspectRatio === '9:16') {
        width = 1080;
        height = 1920;
      }

      canvas.width = width;
      canvas.height = height;
      const ctx = canvas.getContext('2d');
      if (!ctx) return;

      ctx.imageSmoothingEnabled = true;
      ctx.imageSmoothingQuality = 'high';

      // ----------------------------------------------------
      // 1. BASE BACKGROUND & STAR FIELD
      // ----------------------------------------------------
      const bgGrad = ctx.createRadialGradient(width * 0.5, height * 0.45, 100, width * 0.5, height * 0.5, width * 0.85);
      bgGrad.addColorStop(0, '#0E1726');
      bgGrad.addColorStop(0.4, '#070D18');
      bgGrad.addColorStop(0.85, '#03060C');
      bgGrad.addColorStop(1, '#010307');
      ctx.fillStyle = bgGrad;
      ctx.fillRect(0, 0, width, height);

      const pseudoRandom = (seed) => {
        const x = Math.sin(seed) * 10000;
        return x - Math.floor(x);
      };

      ctx.fillStyle = '#FFFFFF';
      for (let i = 0; i < 180; i++) {
        const sx = pseudoRandom(i * 13 + 7) * width;
        const sy = pseudoRandom(i * 29 + 11) * height;
        const size = pseudoRandom(i * 47) * 2.2 + 0.5;
        const alpha = pseudoRandom(i * 31) * 0.6 + 0.15;
        ctx.globalAlpha = alpha;
        ctx.beginPath();
        ctx.arc(sx, sy, size, 0, Math.PI * 2);
        ctx.fill();
      }
      ctx.globalAlpha = 1.0;

      // ----------------------------------------------------
      // 2. ORNATE DUAL METALLIC BORDER & CORNER FLOURISHES
      // ----------------------------------------------------
      const outerMargin = aspectRatio === '9:16' ? 36 : 48;
      const innerMargin = aspectRatio === '9:16' ? 56 : 72;

      // Outer Thin Line
      ctx.strokeStyle = 'rgba(245, 158, 11, 0.4)';
      ctx.lineWidth = 2;
      ctx.strokeRect(outerMargin, outerMargin, width - outerMargin * 2, height - outerMargin * 2);

      // Inner Metallic Gradient Border
      const borderGrad = ctx.createLinearGradient(0, 0, width, height);
      borderGrad.addColorStop(0, tierConfig.borderGrad[0]);
      borderGrad.addColorStop(0.35, tierConfig.borderGrad[1]);
      borderGrad.addColorStop(0.7, tierConfig.borderGrad[2]);
      borderGrad.addColorStop(1, tierConfig.borderGrad[3]);

      ctx.strokeStyle = borderGrad;
      ctx.lineWidth = aspectRatio === '9:16' ? 3 : 3.5;
      ctx.strokeRect(innerMargin, innerMargin, width - innerMargin * 2, height - innerMargin * 2);

      const drawCornerOrnament = (cx, cy, flipX, flipY) => {
        ctx.save();
        ctx.translate(cx, cy);
        ctx.scale(flipX, flipY);
        ctx.strokeStyle = tierConfig.primary;
        ctx.lineWidth = 2.5;
        ctx.beginPath();
        ctx.moveTo(0, 44);
        ctx.lineTo(0, 0);
        ctx.lineTo(44, 0);
        ctx.stroke();

        ctx.beginPath();
        ctx.moveTo(12, 12);
        ctx.lineTo(34, 12);
        ctx.lineTo(12, 34);
        ctx.closePath();
        ctx.stroke();

        ctx.fillStyle = '#38BDF8';
        ctx.beginPath();
        ctx.moveTo(0, -6);
        ctx.lineTo(6, 0);
        ctx.lineTo(0, 6);
        ctx.lineTo(-6, 0);
        ctx.closePath();
        ctx.fill();
        ctx.restore();
      };

      drawCornerOrnament(innerMargin, innerMargin, 1, 1);
      drawCornerOrnament(width - innerMargin, innerMargin, -1, 1);
      drawCornerOrnament(innerMargin, height - innerMargin, 1, -1);
      drawCornerOrnament(width - innerMargin, height - innerMargin, -1, -1);

      const drawCenterCrest = (x, y) => {
        ctx.fillStyle = '#F59E0B';
        ctx.beginPath();
        ctx.moveTo(x, y - 12);
        ctx.lineTo(x + 14, y);
        ctx.lineTo(x, y + 12);
        ctx.lineTo(x - 14, y);
        ctx.closePath();
        ctx.fill();

        ctx.fillStyle = '#38BDF8';
        ctx.beginPath();
        ctx.arc(x, y, 4, 0, Math.PI * 2);
        ctx.fill();
      };

      drawCenterCrest(width / 2, innerMargin);
      drawCenterCrest(width / 2, height - innerMargin);

      // =========================================================================
      // COMPOSITION 1: 16:9 LANDSCAPE (2400 × 1350)
      // Left: Mountain Artwork | Center: Credential Information | Right: Hero Logo
      // =========================================================================
      if (aspectRatio === '16:9') {
        // 1. Mountain Artwork (Left)
        const mtnCenterX = width * 0.165;
        const mtnSummitY = height * 0.42;

        const sunGlow = ctx.createRadialGradient(mtnCenterX, mtnSummitY, 10, mtnCenterX, mtnSummitY, 320);
        sunGlow.addColorStop(0, 'rgba(255, 245, 210, 1)');
        sunGlow.addColorStop(0.15, 'rgba(245, 158, 11, 0.85)');
        sunGlow.addColorStop(0.45, 'rgba(56, 189, 248, 0.35)');
        sunGlow.addColorStop(1, 'transparent');
        ctx.fillStyle = sunGlow;
        ctx.beginPath();
        ctx.arc(mtnCenterX, mtnSummitY, 320, 0, Math.PI * 2);
        ctx.fill();

        ctx.save();
        ctx.translate(mtnCenterX, mtnSummitY);
        for (let ray = 0; ray < 32; ray++) {
          const angle = (ray * Math.PI * 2) / 32;
          const rayLen = 220 + (ray % 2 === 0 ? 120 : 60);
          ctx.strokeStyle = ray % 2 === 0 ? 'rgba(253, 230, 138, 0.28)' : 'rgba(56, 189, 248, 0.18)';
          ctx.lineWidth = ray % 3 === 0 ? 2.5 : 1.2;
          ctx.beginPath();
          ctx.moveTo(0, 0);
          ctx.lineTo(Math.cos(angle) * rayLen, Math.sin(angle) * rayLen);
          ctx.stroke();
        }
        ctx.restore();

        ctx.fillStyle = '#060B14';
        ctx.beginPath();
        ctx.moveTo(width * 0.02, height * 0.88);
        ctx.lineTo(mtnCenterX - 140, height * 0.62);
        ctx.lineTo(mtnCenterX - 70, height * 0.54);
        ctx.lineTo(mtnCenterX, mtnSummitY);
        ctx.lineTo(mtnCenterX + 80, height * 0.56);
        ctx.lineTo(mtnCenterX + 160, height * 0.66);
        ctx.lineTo(mtnCenterX + 280, height * 0.88);
        ctx.closePath();
        ctx.fill();

        ctx.fillStyle = '#0A1222';
        ctx.beginPath();
        ctx.moveTo(mtnCenterX, mtnSummitY);
        ctx.lineTo(mtnCenterX + 80, height * 0.56);
        ctx.lineTo(mtnCenterX + 160, height * 0.66);
        ctx.lineTo(mtnCenterX + 280, height * 0.88);
        ctx.lineTo(mtnCenterX, height * 0.88);
        ctx.closePath();
        ctx.fill();

        ctx.fillStyle = '#0F1A2E';
        ctx.beginPath();
        ctx.moveTo(mtnCenterX, mtnSummitY);
        ctx.lineTo(mtnCenterX - 70, height * 0.54);
        ctx.lineTo(mtnCenterX - 45, height * 0.60);
        ctx.lineTo(mtnCenterX - 110, height * 0.74);
        ctx.lineTo(mtnCenterX - 180, height * 0.88);
        ctx.lineTo(mtnCenterX, height * 0.88);
        ctx.closePath();
        ctx.fill();

        ctx.strokeStyle = 'rgba(253, 230, 138, 0.75)';
        ctx.lineWidth = 2.5;
        ctx.beginPath();
        ctx.moveTo(mtnCenterX - 70, height * 0.54);
        ctx.lineTo(mtnCenterX, mtnSummitY);
        ctx.lineTo(mtnCenterX + 80, height * 0.56);
        ctx.stroke();

        ctx.strokeStyle = 'rgba(245, 158, 11, 0.9)';
        ctx.shadowColor = 'rgba(245, 158, 11, 0.9)';
        ctx.shadowBlur = 16;
        ctx.lineWidth = 4;
        ctx.beginPath();
        ctx.moveTo(mtnCenterX, mtnSummitY);
        ctx.bezierCurveTo(
          mtnCenterX + 35, height * 0.52,
          mtnCenterX - 50, height * 0.62,
          mtnCenterX - 20, height * 0.70
        );
        ctx.bezierCurveTo(
          mtnCenterX + 40, height * 0.78,
          mtnCenterX - 60, height * 0.84,
          mtnCenterX - 30, height * 0.88
        );
        ctx.stroke();
        ctx.shadowBlur = 0;

        const pathPoints = [
          [mtnCenterX, mtnSummitY],
          [mtnCenterX + 18, height * 0.48],
          [mtnCenterX - 12, height * 0.58],
          [mtnCenterX + 10, height * 0.66],
          [mtnCenterX - 15, height * 0.74],
          [mtnCenterX + 12, height * 0.82]
        ];
        ctx.fillStyle = '#FFFFFF';
        pathPoints.forEach(([px, py]) => {
          ctx.beginPath();
          ctx.arc(px, py, 3.5, 0, Math.PI * 2);
          ctx.fill();
        });

        // 2. Official Hero Logo (Right)
        const emblemWidth = 440;
        const emblemHeight = 440;
        const emblemCenterX = width * 0.835;
        const emblemCenterY = height * 0.48;

        const emblemAura = ctx.createRadialGradient(emblemCenterX, emblemCenterY, 30, emblemCenterX, emblemCenterY, emblemWidth * 0.75);
        emblemAura.addColorStop(0, 'rgba(56, 189, 248, 0.45)');
        emblemAura.addColorStop(0.5, 'rgba(59, 130, 246, 0.18)');
        emblemAura.addColorStop(1, 'transparent');
        ctx.fillStyle = emblemAura;
        ctx.beginPath();
        ctx.arc(emblemCenterX, emblemCenterY, emblemWidth * 0.75, 0, Math.PI * 2);
        ctx.fill();

        ctx.strokeStyle = 'rgba(56, 189, 248, 0.35)';
        ctx.lineWidth = 1.5;
        ctx.setLineDash([6, 8]);
        ctx.beginPath();
        ctx.arc(emblemCenterX, emblemCenterY, emblemWidth * 0.55, 0, Math.PI * 2);
        ctx.stroke();
        ctx.setLineDash([]);

        if (heroLogoImgRef.current) {
          ctx.save();
          ctx.shadowColor = 'rgba(56, 189, 248, 0.55)';
          ctx.shadowBlur = 25;
          ctx.drawImage(
            heroLogoImgRef.current,
            emblemCenterX - emblemWidth / 2,
            emblemCenterY - emblemHeight / 2,
            emblemWidth,
            emblemHeight
          );
          ctx.restore();
        }

        // 3. Center Typography
        const contentCenterX = width * 0.50;
        let curY = 160;

        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';

        // Brand Title
        ctx.font = '700 24px "Cinzel", Georgia, serif';
        ctx.fillStyle = '#94A3B8';
        setCanvasLetterSpacing(ctx, '8px');
        ctx.fillText('MASTERY KEY COACH', contentCenterX, curY);

        // Official Mastery Credential
        curY += 54;
        ctx.font = '800 42px "Cinzel", Georgia, serif';
        const headingGrad = ctx.createLinearGradient(contentCenterX - 300, curY, contentCenterX + 300, curY);
        headingGrad.addColorStop(0, '#FFFFFF');
        headingGrad.addColorStop(0.3, tierConfig.light);
        headingGrad.addColorStop(0.7, tierConfig.primary);
        headingGrad.addColorStop(1, '#FFFFFF');
        ctx.fillStyle = headingGrad;
        setCanvasLetterSpacing(ctx, '5px');
        ctx.fillText('OFFICIAL MASTERY CREDENTIAL', contentCenterX, curY);

        // 5 Gold Stars
        curY += 42;
        ctx.font = '800 24px system-ui, sans-serif';
        ctx.fillStyle = '#F59E0B';
        setCanvasLetterSpacing(ctx, '10px');
        ctx.fillText('★ ★ ★ ★ ★', contentCenterX, curY);

        // Certification Subtitle
        curY += 50;
        ctx.font = '600 16px "Cinzel", Georgia, serif';
        ctx.fillStyle = 'rgba(255, 255, 255, 0.7)';
        setCanvasLetterSpacing(ctx, '3px');
        ctx.fillText('THIS IS SERVER-AUTHORITATIVELY CERTIFIED TO', contentCenterX, curY);

        // Recipient Name
        curY += 72;
        const nameFontSize = safeUser.fullName.length > 25 ? 52 : (safeUser.fullName.length > 18 ? 58 : 66);
        ctx.font = `800 ${nameFontSize}px "Cinzel", "Playfair Display", Georgia, serif`;
        const nameGrad = ctx.createLinearGradient(contentCenterX - 320, curY, contentCenterX + 320, curY);
        nameGrad.addColorStop(0, '#FDE68A');
        nameGrad.addColorStop(0.4, '#F59E0B');
        nameGrad.addColorStop(0.8, '#FDE68A');
        nameGrad.addColorStop(1, '#FFFFFF');
        ctx.fillStyle = nameGrad;
        setCanvasLetterSpacing(ctx, '2px');
        ctx.fillText(safeUser.fullName, contentCenterX, curY);

        // Verified Tag & User info
        curY += 46;
        ctx.font = '700 16px monospace';
        ctx.fillStyle = '#38BDF8';
        setCanvasLetterSpacing(ctx, '1.5px');
        ctx.fillText(idTag, contentCenterX, curY);

        // Tier Badge
        curY += 52;
        ctx.font = '800 18px "Cinzel", sans-serif';
        ctx.fillStyle = tierConfig.primary;
        setCanvasLetterSpacing(ctx, '4px');
        ctx.fillText(`✦ ${tierConfig.name} LEVEL ACHIEVEMENT ✦`, contentCenterX, curY);

        // Achievement Title
        curY += 50;
        ctx.font = '800 36px system-ui, -apple-system, sans-serif';
        ctx.fillStyle = '#FFFFFF';
        setCanvasLetterSpacing(ctx, '1px');
        curY = wrapAndRenderText(ctx, safeCredential.title, contentCenterX, curY, 880, 44);

        // Description & Quote
        curY += 36;
        ctx.font = '400 18px system-ui, -apple-system, sans-serif';
        ctx.fillStyle = 'rgba(255, 255, 255, 0.85)';
        setCanvasLetterSpacing(ctx, '0.5px');
        curY = wrapAndRenderText(ctx, safeCredential.description, contentCenterX, curY, 820, 26);

        curY += 36;
        ctx.font = 'italic 400 18px "Playfair Display", Georgia, serif';
        ctx.fillStyle = '#FDE68A';
        setCanvasLetterSpacing(ctx, '0.5px');
        wrapAndRenderText(ctx, quote, contentCenterX, curY, 820, 26);

        // 4. Signatures & Royal Seal Row (16:9)
        const footerY = height - 190;
        const sigSpan = 380;

        // AI Coach Signature (Left)
        const leftSigX = contentCenterX - sigSpan;
        ctx.font = 'italic 32px "Brush Script MT", cursive, Georgia, serif';
        ctx.fillStyle = '#FDE68A';
        setCanvasLetterSpacing(ctx, '1px');
        ctx.fillText('AI Coach Sovereign', leftSigX, footerY - 24);

        ctx.strokeStyle = 'rgba(253, 230, 138, 0.5)';
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.moveTo(leftSigX - 110, footerY - 8);
        ctx.lineTo(leftSigX + 110, footerY - 8);
        ctx.stroke();

        ctx.font = '700 13px "Cinzel", sans-serif';
        ctx.fillStyle = '#FFFFFF';
        setCanvasLetterSpacing(ctx, '2px');
        ctx.fillText('AI COACH PROTOCOL', leftSigX, footerY + 12);
        ctx.font = '500 11px system-ui, sans-serif';
        ctx.fillStyle = 'rgba(255, 255, 255, 0.5)';
        ctx.fillText('DIRECTOR OF TRANSFORMATION', leftSigX, footerY + 28);

        // Royal Laurel Crown Seal (Center)
        const sealRadius = 52;
        const sealGrad = ctx.createRadialGradient(contentCenterX, footerY - 4, 10, contentCenterX, footerY - 4, sealRadius);
        sealGrad.addColorStop(0, '#1E3A8A');
        sealGrad.addColorStop(0.7, '#0F172A');
        sealGrad.addColorStop(1, '#030712');
        ctx.fillStyle = sealGrad;
        ctx.beginPath();
        ctx.arc(contentCenterX, footerY - 4, sealRadius, 0, Math.PI * 2);
        ctx.fill();

        ctx.strokeStyle = '#F59E0B';
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.arc(contentCenterX, footerY - 4, sealRadius - 4, 0, Math.PI * 2);
        ctx.stroke();

        ctx.strokeStyle = 'rgba(245, 158, 11, 0.4)';
        ctx.lineWidth = 1.5;
        ctx.setLineDash([4, 4]);
        ctx.beginPath();
        ctx.arc(contentCenterX, footerY - 4, sealRadius - 10, 0, Math.PI * 2);
        ctx.stroke();
        ctx.setLineDash([]);

        ctx.font = '800 24px system-ui, sans-serif';
        ctx.fillStyle = '#F59E0B';
        ctx.fillText('👑', contentCenterX, footerY - 14);

        ctx.font = '800 10px "Cinzel", sans-serif';
        ctx.fillStyle = '#FDE68A';
        setCanvasLetterSpacing(ctx, '1.5px');
        ctx.fillText('OFFICIAL', contentCenterX, footerY + 12);
        ctx.font = '700 8px monospace';
        ctx.fillStyle = '#38BDF8';
        ctx.fillText('SEAL', contentCenterX, footerY + 24);

        // System Authority Signature (Right)
        const rightSigX = contentCenterX + sigSpan;
        ctx.font = 'italic 32px "Brush Script MT", cursive, Georgia, serif';
        ctx.fillStyle = '#38BDF8';
        setCanvasLetterSpacing(ctx, '1px');
        ctx.fillText('Mastery Key Authority', rightSigX, footerY - 24);

        ctx.strokeStyle = 'rgba(56, 189, 248, 0.5)';
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.moveTo(rightSigX - 110, footerY - 8);
        ctx.lineTo(rightSigX + 110, footerY - 8);
        ctx.stroke();

        ctx.font = '700 13px "Cinzel", sans-serif';
        ctx.fillStyle = '#FFFFFF';
        setCanvasLetterSpacing(ctx, '2px');
        ctx.fillText('SYSTEM VERIFICATION', rightSigX, footerY + 12);
        ctx.font = '500 11px system-ui, sans-serif';
        ctx.fillStyle = 'rgba(255, 255, 255, 0.5)';
        ctx.fillText('MKC MASTER REGISTRAR', rightSigX, footerY + 28);

        // Subfooter Hash & Date (16:9)
        const subFooterY = height - innerMargin - 28;
        ctx.font = '500 16px system-ui, sans-serif';
        ctx.fillStyle = 'rgba(255, 255, 255, 0.65)';
        setCanvasLetterSpacing(ctx, '0.5px');
        ctx.fillText(`Issued on ${issueDateFormatted}  •  +${safeCredential.xpValue} Mastery XP Awarded`, contentCenterX, subFooterY - 22);

        ctx.font = '600 13px monospace';
        ctx.fillStyle = '#F59E0B';
        setCanvasLetterSpacing(ctx, '1px');
        ctx.fillText(`HASH: ${credHash}`, contentCenterX, subFooterY);
      }

      // =========================================================================
      // COMPOSITION 2: 1:1 SQUARE (1800 × 1800)
      // Top: Hero Logo | Center: Credential Information Stack | Lower: Signatures
      // =========================================================================
      else if (aspectRatio === '1:1') {
        const centerX = width * 0.5;

        // 1. Top Hero Logo & Aura (Square)
        const logoWidth = 340;
        const logoHeight = 340;
        const logoCenterY = 320;

        const logoAura = ctx.createRadialGradient(centerX, logoCenterY, 20, centerX, logoCenterY, logoWidth * 0.7);
        logoAura.addColorStop(0, 'rgba(56, 189, 248, 0.45)');
        logoAura.addColorStop(0.5, 'rgba(59, 130, 246, 0.2)');
        logoAura.addColorStop(1, 'transparent');
        ctx.fillStyle = logoAura;
        ctx.beginPath();
        ctx.arc(centerX, logoCenterY, logoWidth * 0.7, 0, Math.PI * 2);
        ctx.fill();

        if (heroLogoImgRef.current) {
          ctx.save();
          ctx.shadowColor = 'rgba(56, 189, 248, 0.55)';
          ctx.shadowBlur = 24;
          ctx.drawImage(
            heroLogoImgRef.current,
            centerX - logoWidth / 2,
            logoCenterY - logoHeight / 2,
            logoWidth,
            logoHeight
          );
          ctx.restore();
        }

        // 2. Brand & Headings
        let curY = 560;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';

        ctx.font = '700 24px "Cinzel", Georgia, serif';
        ctx.fillStyle = '#94A3B8';
        setCanvasLetterSpacing(ctx, '8px');
        ctx.fillText('MASTERY KEY COACH', centerX, curY);

        curY += 56;
        ctx.font = '800 46px "Cinzel", Georgia, serif';
        const headGrad = ctx.createLinearGradient(centerX - 350, curY, centerX + 350, curY);
        headGrad.addColorStop(0, '#FFFFFF');
        headGrad.addColorStop(0.3, tierConfig.light);
        headGrad.addColorStop(0.7, tierConfig.primary);
        headGrad.addColorStop(1, '#FFFFFF');
        ctx.fillStyle = headGrad;
        setCanvasLetterSpacing(ctx, '5px');
        ctx.fillText('OFFICIAL MASTERY CREDENTIAL', centerX, curY);

        curY += 46;
        ctx.font = '800 26px system-ui, sans-serif';
        ctx.fillStyle = '#F59E0B';
        setCanvasLetterSpacing(ctx, '10px');
        ctx.fillText('★ ★ ★ ★ ★', centerX, curY);

        curY += 50;
        ctx.font = '600 17px "Cinzel", Georgia, serif';
        ctx.fillStyle = 'rgba(255, 255, 255, 0.7)';
        setCanvasLetterSpacing(ctx, '3px');
        ctx.fillText('THIS IS SERVER-AUTHORITATIVELY CERTIFIED TO', centerX, curY);

        // Recipient Name
        curY += 80;
        const nameFontSize = safeUser.fullName.length > 25 ? 54 : (safeUser.fullName.length > 18 ? 62 : 70);
        ctx.font = `800 ${nameFontSize}px "Cinzel", "Playfair Display", Georgia, serif`;
        const nameGrad = ctx.createLinearGradient(centerX - 350, curY, centerX + 350, curY);
        nameGrad.addColorStop(0, '#FDE68A');
        nameGrad.addColorStop(0.4, '#F59E0B');
        nameGrad.addColorStop(0.8, '#FDE68A');
        nameGrad.addColorStop(1, '#FFFFFF');
        ctx.fillStyle = nameGrad;
        setCanvasLetterSpacing(ctx, '2px');
        ctx.fillText(safeUser.fullName, centerX, curY);

        // Verified Tag
        curY += 50;
        ctx.font = '700 17px monospace';
        ctx.fillStyle = '#38BDF8';
        setCanvasLetterSpacing(ctx, '1.5px');
        ctx.fillText(idTag, centerX, curY);

        // Tier
        curY += 54;
        ctx.font = '800 20px "Cinzel", sans-serif';
        ctx.fillStyle = tierConfig.primary;
        setCanvasLetterSpacing(ctx, '4px');
        ctx.fillText(`✦ ${tierConfig.name} LEVEL ACHIEVEMENT ✦`, centerX, curY);

        // Title
        curY += 54;
        ctx.font = '800 38px system-ui, -apple-system, sans-serif';
        ctx.fillStyle = '#FFFFFF';
        setCanvasLetterSpacing(ctx, '1px');
        curY = wrapAndRenderText(ctx, safeCredential.title, centerX, curY, 1300, 46);

        // Description
        curY += 38;
        ctx.font = '400 20px system-ui, -apple-system, sans-serif';
        ctx.fillStyle = 'rgba(255, 255, 255, 0.85)';
        setCanvasLetterSpacing(ctx, '0.5px');
        curY = wrapAndRenderText(ctx, safeCredential.description, centerX, curY, 1200, 30);

        // Quote
        curY += 40;
        ctx.font = 'italic 400 20px "Playfair Display", Georgia, serif';
        ctx.fillStyle = '#FDE68A';
        setCanvasLetterSpacing(ctx, '0.5px');
        wrapAndRenderText(ctx, quote, centerX, curY, 1200, 30);

        // 3. Signatures & Royal Seal (Square)
        const footerY = height - 260;
        const sigSpan = 440;

        // AI Coach Signature (Left)
        const leftSigX = centerX - sigSpan;
        ctx.font = 'italic 34px "Brush Script MT", cursive, Georgia, serif';
        ctx.fillStyle = '#FDE68A';
        setCanvasLetterSpacing(ctx, '1px');
        ctx.fillText('AI Coach Sovereign', leftSigX, footerY - 24);

        ctx.strokeStyle = 'rgba(253, 230, 138, 0.5)';
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.moveTo(leftSigX - 120, footerY - 8);
        ctx.lineTo(leftSigX + 120, footerY - 8);
        ctx.stroke();

        ctx.font = '700 13px "Cinzel", sans-serif';
        ctx.fillStyle = '#FFFFFF';
        setCanvasLetterSpacing(ctx, '2px');
        ctx.fillText('AI COACH PROTOCOL', leftSigX, footerY + 12);
        ctx.font = '500 11px system-ui, sans-serif';
        ctx.fillStyle = 'rgba(255, 255, 255, 0.5)';
        ctx.fillText('DIRECTOR OF TRANSFORMATION', leftSigX, footerY + 28);

        // Royal Laurel Crown Seal (Center)
        const sealRadius = 56;
        const sealGrad = ctx.createRadialGradient(centerX, footerY - 4, 10, centerX, footerY - 4, sealRadius);
        sealGrad.addColorStop(0, '#1E3A8A');
        sealGrad.addColorStop(0.7, '#0F172A');
        sealGrad.addColorStop(1, '#030712');
        ctx.fillStyle = sealGrad;
        ctx.beginPath();
        ctx.arc(centerX, footerY - 4, sealRadius, 0, Math.PI * 2);
        ctx.fill();

        ctx.strokeStyle = '#F59E0B';
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.arc(centerX, footerY - 4, sealRadius - 4, 0, Math.PI * 2);
        ctx.stroke();

        ctx.strokeStyle = 'rgba(245, 158, 11, 0.4)';
        ctx.lineWidth = 1.5;
        ctx.setLineDash([4, 4]);
        ctx.beginPath();
        ctx.arc(centerX, footerY - 4, sealRadius - 10, 0, Math.PI * 2);
        ctx.stroke();
        ctx.setLineDash([]);

        ctx.font = '800 26px system-ui, sans-serif';
        ctx.fillStyle = '#F59E0B';
        ctx.fillText('👑', centerX, footerY - 14);

        ctx.font = '800 10px "Cinzel", sans-serif';
        ctx.fillStyle = '#FDE68A';
        setCanvasLetterSpacing(ctx, '1.5px');
        ctx.fillText('OFFICIAL', centerX, footerY + 12);
        ctx.font = '700 8px monospace';
        ctx.fillStyle = '#38BDF8';
        ctx.fillText('SEAL', centerX, footerY + 24);

        // System Authority Signature (Right)
        const rightSigX = centerX + sigSpan;
        ctx.font = 'italic 34px "Brush Script MT", cursive, Georgia, serif';
        ctx.fillStyle = '#38BDF8';
        setCanvasLetterSpacing(ctx, '1px');
        ctx.fillText('Mastery Key Authority', rightSigX, footerY - 24);

        ctx.strokeStyle = 'rgba(56, 189, 248, 0.5)';
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.moveTo(rightSigX - 120, footerY - 8);
        ctx.lineTo(rightSigX + 120, footerY - 8);
        ctx.stroke();

        ctx.font = '700 13px "Cinzel", sans-serif';
        ctx.fillStyle = '#FFFFFF';
        setCanvasLetterSpacing(ctx, '2px');
        ctx.fillText('SYSTEM VERIFICATION', rightSigX, footerY + 12);
        ctx.font = '500 11px system-ui, sans-serif';
        ctx.fillStyle = 'rgba(255, 255, 255, 0.5)';
        ctx.fillText('MKC MASTER REGISTRAR', rightSigX, footerY + 28);

        // Subfooter (1:1)
        const subFooterY = height - innerMargin - 32;
        ctx.font = '500 17px system-ui, sans-serif';
        ctx.fillStyle = 'rgba(255, 255, 255, 0.65)';
        setCanvasLetterSpacing(ctx, '0.5px');
        ctx.fillText(`Issued on ${issueDateFormatted}  •  +${safeCredential.xpValue} Mastery XP Awarded`, centerX, subFooterY - 24);

        ctx.font = '600 13px monospace';
        ctx.fillStyle = '#F59E0B';
        setCanvasLetterSpacing(ctx, '1px');
        ctx.fillText(`HASH: ${credHash}`, centerX, subFooterY);
      }

      // =========================================================================
      // COMPOSITION 3: 9:16 PORTRAIT (1080 × 1920)
      // Top: Hero Logo | Card: Vertically Stacked Typography | Lower: Seal & Signatures
      // =========================================================================
      else if (aspectRatio === '9:16') {
        const centerX = width * 0.5;

        // 1. Top Hero Logo & Aura (Portrait)
        const logoWidth = 300;
        const logoHeight = 300;
        const logoCenterY = 270;

        const logoAura = ctx.createRadialGradient(centerX, logoCenterY, 20, centerX, logoCenterY, logoWidth * 0.7);
        logoAura.addColorStop(0, 'rgba(56, 189, 248, 0.45)');
        logoAura.addColorStop(0.5, 'rgba(59, 130, 246, 0.2)');
        logoAura.addColorStop(1, 'transparent');
        ctx.fillStyle = logoAura;
        ctx.beginPath();
        ctx.arc(centerX, logoCenterY, logoWidth * 0.7, 0, Math.PI * 2);
        ctx.fill();

        if (heroLogoImgRef.current) {
          ctx.save();
          ctx.shadowColor = 'rgba(56, 189, 248, 0.55)';
          ctx.shadowBlur = 22;
          ctx.drawImage(
            heroLogoImgRef.current,
            centerX - logoWidth / 2,
            logoCenterY - logoHeight / 2,
            logoWidth,
            logoHeight
          );
          ctx.restore();
        }

        // 2. Brand & Headings
        let curY = 480;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';

        ctx.font = '700 20px "Cinzel", Georgia, serif';
        ctx.fillStyle = '#94A3B8';
        setCanvasLetterSpacing(ctx, '7px');
        ctx.fillText('MASTERY KEY COACH', centerX, curY);

        curY += 52;
        ctx.font = '800 36px "Cinzel", Georgia, serif';
        const headGrad = ctx.createLinearGradient(centerX - 280, curY, centerX + 280, curY);
        headGrad.addColorStop(0, '#FFFFFF');
        headGrad.addColorStop(0.3, tierConfig.light);
        headGrad.addColorStop(0.7, tierConfig.primary);
        headGrad.addColorStop(1, '#FFFFFF');
        ctx.fillStyle = headGrad;
        setCanvasLetterSpacing(ctx, '4px');
        ctx.fillText('OFFICIAL MASTERY CREDENTIAL', centerX, curY);

        curY += 42;
        ctx.font = '800 22px system-ui, sans-serif';
        ctx.fillStyle = '#F59E0B';
        setCanvasLetterSpacing(ctx, '8px');
        ctx.fillText('★ ★ ★ ★ ★', centerX, curY);

        curY += 46;
        ctx.font = '600 15px "Cinzel", Georgia, serif';
        ctx.fillStyle = 'rgba(255, 255, 255, 0.7)';
        setCanvasLetterSpacing(ctx, '2px');
        ctx.fillText('SERVER-AUTHORITATIVELY CERTIFIED TO', centerX, curY);

        // Recipient Name
        curY += 72;
        const nameFontSize = safeUser.fullName.length > 25 ? 46 : (safeUser.fullName.length > 18 ? 54 : 62);
        ctx.font = `800 ${nameFontSize}px "Cinzel", "Playfair Display", Georgia, serif`;
        const nameGrad = ctx.createLinearGradient(centerX - 280, curY, centerX + 280, curY);
        nameGrad.addColorStop(0, '#FDE68A');
        nameGrad.addColorStop(0.4, '#F59E0B');
        nameGrad.addColorStop(0.8, '#FDE68A');
        nameGrad.addColorStop(1, '#FFFFFF');
        ctx.fillStyle = nameGrad;
        setCanvasLetterSpacing(ctx, '2px');
        ctx.fillText(safeUser.fullName, centerX, curY);

        // Verified Tag
        curY += 46;
        ctx.font = '700 15px monospace';
        ctx.fillStyle = '#38BDF8';
        setCanvasLetterSpacing(ctx, '1.5px');
        ctx.fillText(idTag, centerX, curY);

        // Tier
        curY += 48;
        ctx.font = '800 17px "Cinzel", sans-serif';
        ctx.fillStyle = tierConfig.primary;
        setCanvasLetterSpacing(ctx, '3px');
        ctx.fillText(`✦ ${tierConfig.name} LEVEL ACHIEVEMENT ✦`, centerX, curY);

        // Title
        curY += 50;
        ctx.font = '800 32px system-ui, -apple-system, sans-serif';
        ctx.fillStyle = '#FFFFFF';
        setCanvasLetterSpacing(ctx, '0.5px');
        curY = wrapAndRenderText(ctx, safeCredential.title, centerX, curY, 820, 40);

        // Description
        curY += 34;
        ctx.font = '400 17px system-ui, -apple-system, sans-serif';
        ctx.fillStyle = 'rgba(255, 255, 255, 0.85)';
        setCanvasLetterSpacing(ctx, '0.5px');
        curY = wrapAndRenderText(ctx, safeCredential.description, centerX, curY, 780, 26);

        // Quote
        curY += 34;
        ctx.font = 'italic 400 17px "Playfair Display", Georgia, serif';
        ctx.fillStyle = '#FDE68A';
        setCanvasLetterSpacing(ctx, '0.5px');
        wrapAndRenderText(ctx, quote, centerX, curY, 780, 26);

        // 3. Signatures & Royal Seal (Portrait)
        const footerY = height - 250;
        const sigSpan = 290;

        // AI Coach Signature (Left)
        const leftSigX = centerX - sigSpan;
        ctx.font = 'italic 26px "Brush Script MT", cursive, Georgia, serif';
        ctx.fillStyle = '#FDE68A';
        setCanvasLetterSpacing(ctx, '1px');
        ctx.fillText('AI Coach', leftSigX, footerY - 20);

        ctx.strokeStyle = 'rgba(253, 230, 138, 0.5)';
        ctx.lineWidth = 1.2;
        ctx.beginPath();
        ctx.moveTo(leftSigX - 80, footerY - 6);
        ctx.lineTo(leftSigX + 80, footerY - 6);
        ctx.stroke();

        ctx.font = '700 11px "Cinzel", sans-serif';
        ctx.fillStyle = '#FFFFFF';
        setCanvasLetterSpacing(ctx, '2px');
        ctx.fillText('COACH PROTOCOL', leftSigX, footerY + 12);
        ctx.font = '500 10px system-ui, sans-serif';
        ctx.fillStyle = 'rgba(255, 255, 255, 0.5)';
        ctx.fillText('MASTER DIRECTOR', leftSigX, footerY + 26);

        // Royal Laurel Crown Seal (Center)
        const sealRadius = 50;
        const sealGrad = ctx.createRadialGradient(centerX, footerY - 4, 10, centerX, footerY - 4, sealRadius);
        sealGrad.addColorStop(0, '#1E3A8A');
        sealGrad.addColorStop(0.7, '#0F172A');
        sealGrad.addColorStop(1, '#030712');
        ctx.fillStyle = sealGrad;
        ctx.beginPath();
        ctx.arc(centerX, footerY - 4, sealRadius, 0, Math.PI * 2);
        ctx.fill();

        ctx.strokeStyle = '#F59E0B';
        ctx.lineWidth = 2.5;
        ctx.beginPath();
        ctx.arc(centerX, footerY - 4, sealRadius - 4, 0, Math.PI * 2);
        ctx.stroke();

        ctx.strokeStyle = 'rgba(245, 158, 11, 0.4)';
        ctx.lineWidth = 1.2;
        ctx.setLineDash([3, 3]);
        ctx.beginPath();
        ctx.arc(centerX, footerY - 4, sealRadius - 9, 0, Math.PI * 2);
        ctx.stroke();
        ctx.setLineDash([]);

        ctx.font = '800 22px system-ui, sans-serif';
        ctx.fillStyle = '#F59E0B';
        ctx.fillText('👑', centerX, footerY - 12);

        ctx.font = '800 9px "Cinzel", sans-serif';
        ctx.fillStyle = '#FDE68A';
        setCanvasLetterSpacing(ctx, '1.5px');
        ctx.fillText('OFFICIAL', centerX, footerY + 10);
        ctx.font = '700 8px monospace';
        ctx.fillStyle = '#38BDF8';
        ctx.fillText('SEAL', centerX, footerY + 22);

        // System Authority Signature (Right)
        const rightSigX = centerX + sigSpan;
        ctx.font = 'italic 26px "Brush Script MT", cursive, Georgia, serif';
        ctx.fillStyle = '#38BDF8';
        setCanvasLetterSpacing(ctx, '1px');
        ctx.fillText('MKC Registrar', rightSigX, footerY - 20);

        ctx.strokeStyle = 'rgba(56, 189, 248, 0.5)';
        ctx.lineWidth = 1.2;
        ctx.beginPath();
        ctx.moveTo(rightSigX - 80, footerY - 6);
        ctx.lineTo(rightSigX + 80, footerY - 6);
        ctx.stroke();

        ctx.font = '700 11px "Cinzel", sans-serif';
        ctx.fillStyle = '#FFFFFF';
        setCanvasLetterSpacing(ctx, '2px');
        ctx.fillText('SYSTEM VERIFY', rightSigX, footerY + 12);
        ctx.font = '500 10px system-ui, sans-serif';
        ctx.fillStyle = 'rgba(255, 255, 255, 0.5)';
        ctx.fillText('MASTER AUTHORITY', rightSigX, footerY + 26);

        // Subfooter (9:16)
        const subFooterY = height - innerMargin - 32;
        ctx.font = '500 15px system-ui, sans-serif';
        ctx.fillStyle = 'rgba(255, 255, 255, 0.65)';
        setCanvasLetterSpacing(ctx, '0.5px');
        ctx.fillText(`Issued on ${issueDateFormatted}  •  +${safeCredential.xpValue} Mastery XP Awarded`, centerX, subFooterY - 22);

        ctx.font = '600 12px monospace';
        ctx.fillStyle = '#F59E0B';
        setCanvasLetterSpacing(ctx, '1px');
        ctx.fillText(`HASH: ${credHash}`, centerX, subFooterY);
      }
    } catch (err) {
      console.error('Certificate preview render failed:', err);
      throw err;
    }
  }, [aspectRatio, credential, idTag, issueDateFormatted, credHash, quote, safeCredential.description, safeCredential.title, safeCredential.xpValue, safeUser.fullName, tierConfig]);

  // Re-render when dependencies or logo changes
  useEffect(() => {
    try {
      renderCertificate();
    } catch (err) {
      console.error('Certificate preview render failed:', err);
    }
  }, [renderCertificate, logoLoaded]);

  // Download High-Resolution PNG
  const handleDownload = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    try {
      const link = document.createElement('a');
      const slug = (safeCredential.slug || 'credential').toLowerCase();
      const ratioStr = aspectRatio.replace(':', 'x');
      link.download = `MKC_Mastery_Credential_${slug}_${ratioStr}.png`;
      link.href = canvas.toDataURL('image/png', 1.0);
      link.click();
    } catch (err) {
      console.error('Download failed:', err);
    }
  };

  // Copy Public Verification Link
  const handleCopyLink = () => {
    try {
      const origin = window.location.origin;
      const credId = safeCredential.id || 1;
      const publicUrl = `${origin}/profile?cred=${credId}`;
      navigator.clipboard.writeText(publicUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    } catch (err) {
      console.error('Failed to copy link:', err);
    }
  };

  if (!credential) {
    return (
      <div className="cert-modal-backdrop" onClick={onClose} role="dialog" aria-modal="true">
        <div className="cert-modal-card glass-panel" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '480px', textAlign: 'center' }}>
          <div className="cert-modal-header">
            <div className="cert-header-title">
              <div className="cert-header-badge">
                <Award size={22} style={{ color: '#F59E0B' }} />
              </div>
              <div>
                <h3>Mastery Credential</h3>
                <span className="cert-header-sub">Credential Notice</span>
              </div>
            </div>
            <button onClick={onClose} className="cert-close-btn" aria-label="Close modal"><X size={18} /></button>
          </div>
          <div style={{ padding: '36px 20px', color: '#94A3B8' }}>
            <AlertTriangle size={36} color="#F59E0B" style={{ margin: '0 auto 14px' }} />
            <p style={{ margin: '0 0 20px 0', fontSize: '14px', lineHeight: '1.6' }}>
              Credential information is currently unavailable or record is incomplete.
            </p>
            <button onClick={onClose} className="cert-btn btn-primary" style={{ marginInline: 'auto' }}>
              Close Preview
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="cert-modal-backdrop" onClick={onClose} role="dialog" aria-modal="true">
      <div 
        className="cert-modal-card glass-panel" 
        onClick={(e) => e.stopPropagation()}
      >
        {/* MODAL HEADER */}
        <div className="cert-modal-header">
          <div className="cert-header-title">
            <div className="cert-header-badge">
              <Award size={22} style={{ color: '#F59E0B' }} />
            </div>
            <div>
              <h3>Official Mastery Credential</h3>
              <div className="cert-header-sub-row">
                <span className="cert-header-sub">Server-verified proof of discipline & execution</span>
                <span className="cert-verified-pill">
                  <ShieldCheck size={13} strokeWidth={2.4} />
                  <span>VERIFIED</span>
                </span>
              </div>
            </div>
          </div>
          <button 
            onClick={onClose} 
            className="cert-close-btn" 
            aria-label="Close certificate modal"
            title="Close (Esc)"
          >
            <X size={18} />
          </button>
        </div>

        {/* EXPORT FORMAT SELECTOR */}
        <div className="cert-aspect-selector">
          <span className="aspect-label">EXPORT FORMAT:</span>
          <button 
            className={`aspect-btn ${aspectRatio === '16:9' ? 'active' : ''}`}
            onClick={() => setAspectRatio('16:9')}
            title="16:9 Landscape for LinkedIn and X / Twitter"
          >
            16:9 (LinkedIn / X)
          </button>
          <button 
            className={`aspect-btn ${aspectRatio === '1:1' ? 'active' : ''}`}
            onClick={() => setAspectRatio('1:1')}
            title="1:1 Square for Instagram and Feed Posts"
          >
            1:1 (Post / Square)
          </button>
          <button 
            className={`aspect-btn ${aspectRatio === '9:16' ? 'active' : ''}`}
            onClick={() => setAspectRatio('9:16')}
            title="9:16 Vertical for Stories, Reels and Shorts"
          >
            9:16 (Story / Reels)
          </button>
        </div>

        {/* CERTIFICATE PREVIEW CONTAINER */}
        <div className="cert-canvas-container">
          <canvas 
            ref={canvasRef} 
            className={`cert-canvas aspect-${aspectRatio.replace(':', '-')}`} 
          />
        </div>

        {/* MODAL FOOTER ACTIONS */}
        <div className="cert-modal-footer">
          <button 
            onClick={handleCopyLink} 
            className="cert-btn btn-secondary"
            title="Copy Public Verification Link"
          >
            {copied ? <Check size={16} /> : <Copy size={16} />}
            <span>{copied ? 'Link Copied!' : 'Share Link'}</span>
          </button>
          <button 
            onClick={handleDownload} 
            className="cert-btn btn-primary"
            title="Download High-Resolution Certificate (PNG)"
          >
            <Download size={16} />
            <span>Download Certificate (PNG)</span>
          </button>
        </div>
      </div>
    </div>
  );
}
