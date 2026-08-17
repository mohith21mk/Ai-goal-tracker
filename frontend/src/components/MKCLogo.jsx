import React, { useId } from "react";

export const MKC_LOGO_SVG_STRING = `
<svg
  viewBox="0 0 1254 1254"
  xmlns="http://www.w3.org/2000/svg"
  role="img"
  aria-label="Mastery Key Coach logo"
>
  <defs>

    <!-- =====================================================
         PRIMARY METALLIC SAPPHIRE
    ====================================================== -->

    <linearGradient
      id="mkcPrimary"
      x1="0"
      y1="0"
      x2="1"
      y2="1"
    >
      <stop offset="0%" stop-color="#FFFFFF"/>
      <stop offset="8%" stop-color="#F9FCFF"/>
      <stop offset="20%" stop-color="#D9EBFF"/>
      <stop offset="34%" stop-color="#76BAFF"/>
      <stop offset="48%" stop-color="#278AF7"/>
      <stop offset="63%" stop-color="#1268DA"/>
      <stop offset="78%" stop-color="#0A499F"/>
      <stop offset="91%" stop-color="#063574"/>
      <stop offset="100%" stop-color="#02142F"/>
    </linearGradient>


    <!-- =====================================================
         BRIGHT ICE METAL
    ====================================================== -->

    <linearGradient
      id="mkcBright"
      x1="0"
      y1="0"
      x2="1"
      y2="1"
    >
      <stop offset="0%" stop-color="#FFFFFF"/>
      <stop offset="14%" stop-color="#FFFFFF"/>
      <stop offset="30%" stop-color="#EFF7FF"/>
      <stop offset="47%" stop-color="#CAE3FF"/>
      <stop offset="63%" stop-color="#6CB2FF"/>
      <stop offset="80%" stop-color="#2A87EE"/>
      <stop offset="100%" stop-color="#0A54B8"/>
    </linearGradient>


    <!-- =====================================================
         DEEP SAPPHIRE
    ====================================================== -->

    <linearGradient
      id="mkcDeep"
      x1="0"
      y1="0"
      x2="0"
      y2="1"
    >
      <stop offset="0%" stop-color="#2F95FF"/>
      <stop offset="20%" stop-color="#146BDD"/>
      <stop offset="40%" stop-color="#0B4BA7"/>
      <stop offset="62%" stop-color="#063576"/>
      <stop offset="82%" stop-color="#031F4A"/>
      <stop offset="100%" stop-color="#010A20"/>
    </linearGradient>


    <!-- =====================================================
         CENTER LIGHT
    ====================================================== -->

    <linearGradient
      id="mkcCenterLight"
      x1="0"
      y1="0"
      x2="0"
      y2="1"
    >
      <stop offset="0%" stop-color="#FFFFFF"/>
      <stop offset="20%" stop-color="#F5FAFF"/>
      <stop offset="42%" stop-color="#C4E1FF"/>
      <stop offset="61%" stop-color="#69B2FF"/>
      <stop offset="80%" stop-color="#1D77E8"/>
      <stop offset="100%" stop-color="#0A469D"/>
    </linearGradient>


    <!-- =====================================================
         STAR
    ====================================================== -->

    <radialGradient id="mkcStar">
      <stop offset="0%" stop-color="#FFFFFF"/>
      <stop offset="30%" stop-color="#FFFFFF"/>
      <stop offset="52%" stop-color="#EEF8FF"/>
      <stop offset="72%" stop-color="#A9D5FF"/>
      <stop offset="88%" stop-color="#58AAFF"/>
      <stop offset="100%" stop-color="#2177E7"/>
    </radialGradient>


    <!-- =====================================================
         ONE CONTINUOUS SWORD
    ====================================================== -->

    <linearGradient
      id="mkcSword"
      x1="0"
      y1="0"
      x2="1"
      y2="0"
    >
      <stop offset="0%" stop-color="#021532"/>
      <stop offset="18%" stop-color="#0A3B80"/>
      <stop offset="34%" stop-color="#1B77E5"/>
      <stop offset="46%" stop-color="#65AFFF"/>
      <stop offset="50%" stop-color="#FFFFFF"/>
      <stop offset="54%" stop-color="#69B3FF"/>
      <stop offset="66%" stop-color="#1A76E2"/>
      <stop offset="82%" stop-color="#0A3B80"/>
      <stop offset="100%" stop-color="#021532"/>
    </linearGradient>


    <!-- =====================================================
         WARM TIP
    ====================================================== -->

    <linearGradient
      id="mkcTip"
      x1="0"
      y1="0"
      x2="0"
      y2="1"
    >
      <stop offset="0%" stop-color="#FFFFFF"/>
      <stop offset="38%" stop-color="#FFF8DE"/>
      <stop offset="68%" stop-color="#F0CA65"/>
      <stop offset="100%" stop-color="#AD7518"/>
    </linearGradient>


    <!-- =====================================================
         GLOW
    ====================================================== -->

    <filter
      id="mkcGlow"
      x="-35%"
      y="-35%"
      width="170%"
      height="170%"
    >
      <feGaussianBlur
        stdDeviation="3"
        result="blur"
      />

      <feColorMatrix
        in="blur"
        type="matrix"
        values="
          0 0 0 0 0.03
          0 0 0 0 0.32
          0 0 0 0 0.95
          0 0 0 0.58 0
        "
        result="blueGlow"
      />

      <feMerge>
        <feMergeNode in="blueGlow"/>
        <feMergeNode in="SourceGraphic"/>
      </feMerge>
    </filter>


    <!-- =====================================================
         CORE GLOW
    ====================================================== -->

    <filter
      id="mkcCoreGlow"
      x="-50%"
      y="-50%"
      width="200%"
      height="200%"
    >
      <feGaussianBlur stdDeviation="8"/>
    </filter>

  </defs>


  <!-- =====================================================
       CENTER ATMOSPHERE
  ====================================================== -->

  <ellipse
    cx="627"
    cy="620"
    rx="285"
    ry="345"
    fill="#0E61D4"
    opacity="0.06"
    filter="url(#mkcCoreGlow)"
  />


  <!-- =====================================================
       1. TOP DIAMOND
  ====================================================== -->

  <g
    transform="translate(75.24,20) scale(0.88,0.88)"
    filter="url(#mkcGlow)"
  >

    <path
      d="
        M627 42
        C591 94 550 130 505 158
        C550 183 588 215 609 252
        C619 270 624 286 627 306
        C630 286 635 270 645 252
        C666 215 704 183 749 158
        C704 130 663 94 627 42
        Z
      "
      fill="none"
      stroke="url(#mkcPrimary)"
      stroke-width="19"
      stroke-linejoin="miter"
    />

    <path
      d="
        M627 104
        C623 132 613 148 584 157
        C613 163 623 174 627 210
        C631 174 641 163 670 157
        C641 148 631 132 627 104
        Z
      "
      fill="url(#mkcStar)"
    />

  </g>


  <!-- =====================================================
       2. CROSSBAR
  ====================================================== -->

  <g filter="url(#mkcGlow)">

    <path
      d="
        M375 261
        L568 261
        L565 286
        L405 286
        L414 300
        L567 328
        L394 307
        Z
      "
      fill="url(#mkcPrimary)"
    />

    <path
      d="
        M686 261
        L879 261
        L860 307
        L687 328
        L840 300
        L849 286
        L689 286
        Z
      "
      fill="url(#mkcPrimary)"
    />

    <path
      d="M388 268 L548 268"
      fill="none"
      stroke="#FFFFFF"
      stroke-width="3"
      opacity="0.42"
      stroke-linecap="round"
    />

    <path
      d="M706 268 L866 268"
      fill="none"
      stroke="#FFFFFF"
      stroke-width="3"
      opacity="0.42"
      stroke-linecap="round"
    />

  </g>


  <!-- =====================================================
       3. ANCHOR
       
       Slightly narrower than previous version.
       Height preserved.
  ====================================================== -->

  <g
    transform="translate(62, -10) scale(0.90, 1.025)"
    filter="url(#mkcGlow)"
  >

    <!-- LEFT OUTER FLUKE -->

    <path
      d="
        M246 548

        C216 596 196 654 197 710

        C198 761 210 806 224 840

        C229 807 240 780 259 755

        C247 779 241 801 242 820

        C285 878 346 915 423 935

        C355 902 305 858 276 806

        C247 755 232 704 236 653

        C239 613 244 579 246 548

        Z
      "
      fill="url(#mkcBright)"
    />


    <!-- RIGHT OUTER FLUKE -->

    <path
      d="
        M1004 548

        C1034 596 1054 654 1057 710

        C1056 761 1044 806 1030 840

        C1025 807 1014 780 995 755

        C1007 779 1013 801 1012 820

        C969 878 908 915 831 935

        C899 902 949 858 978 806

        C1007 755 1022 704 1018 653

        C1015 613 1010 579 1004 548

        Z
      "
      fill="url(#mkcBright)"
    />


    <!-- LEFT INNER CURVE -->

    <path
      d="
        M287 649

        C305 717 348 774 406 808

        C454 836 509 848 552 837

        C584 829 599 806 599 761

        L599 599

        L627 571

        L627 849

        C627 880 608 901 580 914

        C519 942 448 925 388 890

        C326 853 284 793 267 720

        C260 689 262 666 287 649

        Z
      "
      fill="url(#mkcPrimary)"
    />


    <!-- RIGHT INNER CURVE -->

    <path
      d="
        M963 649

        C945 717 902 774 844 808

        C796 836 741 848 702 837

        C670 829 655 806 655 761

        L655 599

        L627 571

        L627 849

        C627 880 646 901 674 914

        C731 942 802 925 862 890

        C924 853 966 793 983 720

        C990 689 988 666 963 649

        Z
      "
      fill="url(#mkcPrimary)"
    />

  </g>


  <!-- =====================================================
       4. OUTER SWEEP
  ====================================================== -->

  <g
    transform="translate(62, -5) scale(0.90, 1.025)"
    fill="none"
    stroke="url(#mkcPrimary)"
    stroke-linecap="round"
    filter="url(#mkcGlow)"
  >

    <path
      d="
        M221 770

        C257 851 323 908 411 948

        C493 985 559 1006 627 1075

        C695 1006 759 985 839 948

        C927 908 993 851 1029 770
      "
      stroke-width="19"
    />

    <path
      d="
        M246 810

        C291 879 348 919 425 950

        C503 981 567 1001 627 1058

        C687 1001 749 981 825 950

        C902 919 959 879 1004 810
      "
      stroke-width="11"
    />

  </g>


  <!-- =====================================================
       5. ONE CONTINUOUS CENTER SWORD
  ====================================================== -->

  <g filter="url(#mkcGlow)">

    <path
      d="
        M600 240

        L610 205
        L627 182
        L644 205
        L654 240

        L654 478

        L646 505

        L646 888

        L627 925

        L608 888

        L608 505

        L600 478

        Z
      "
      fill="url(#mkcSword)"
    />


    <path
      d="
        M627 205

        L638 239
        L638 482

        L637 505
        L637 882

        L627 905

        L617 882
        L617 505

        L616 482
        L616 239

        Z
      "
      fill="url(#mkcCenterLight)"
      opacity="0.88"
    />


    <path
      d="
        M627 205
        L627 905
      "
      fill="none"
      stroke="#FFFFFF"
      stroke-width="2.5"
      opacity="0.78"
      stroke-linecap="round"
    />

  </g>


  <!-- =====================================================
       6. M + K
       
       Still ONE joined MK group.
       K left stem slightly narrowed so M remains
       more visible without separating M and K.
  ====================================================== -->

  <g
    transform="translate(120,30) scale(0.86,0.94)"
    filter="url(#mkcGlow)"
    fill="url(#mkcBright)"
  >

    <!-- M -->

    <path
      d="
        M263 372

        L331 372
        L412 468
        L494 372
        L548 372

        L548 628

        L487 628
        L487 461

        L425 538
        L401 538

        L335 461

        L335 628
        L263 628

        Z
      "
    />


    <!-- K
         Slightly narrower left stem
    -->

    <path
      d="
        M493 372

        L548 372
        L548 474

        L630 372
        L720 372

        L632 490

        L730 628

        L666 628

        L595 532

        L548 566

        L548 628

        L493 628

        Z
      "
    />

  </g>


  <!-- =====================================================
       7. C
       UNCHANGED
  ====================================================== -->

  <g
    transform="translate(83.91,30) scale(0.86,0.94)"
    filter="url(#mkcGlow)"
    fill="url(#mkcBright)"
  >

    <path
      d="
        M960 372

        L960 430
        L850 430

        C815 430 796 448 796 482

        L796 522

        C796 556 815 574 850 574

        L960 574

        L960 628
        L834 628

        C766 628 730 590 730 522

        L730 478

        C730 410 766 372 834 372

        Z
      "
    />

  </g>


  <!-- =====================================================
       8. M + K HIGHLIGHTS
  ====================================================== -->

  <g
    transform="translate(120,30) scale(0.86,0.94)"
    fill="none"
    stroke="#FFFFFF"
    stroke-width="3"
    opacity="0.48"
    stroke-linecap="round"
  >

    <path
      d="
        M278 383
        L328 383
        L412 480
        L490 383
      "
    />

    <path
      d="
        M503 383
        L540 383
        L540 487
      "
    />

  </g>


  <!-- =====================================================
       9. C HIGHLIGHT
  ====================================================== -->

  <g
    transform="translate(83.91,30) scale(0.86,0.94)"
    fill="none"
    stroke="#FFFFFF"
    stroke-width="3"
    opacity="0.48"
    stroke-linecap="round"
  >

    <path
      d="
        M842 383
        L948 383
      "
    />

  </g>


  <!-- =====================================================
       10. BOTTOM DIAMOND
  ====================================================== -->

  <path
    d="
      M627 905

      L678 959

      L627 1030

      L576 959

      Z
    "
    fill="url(#mkcDeep)"
    filter="url(#mkcGlow)"
  />


  <path
    d="
      M627 920

      L662 959

      L627 1008

      L592 959

      Z
    "
    fill="none"
    stroke="#5DAAFF"
    stroke-width="3"
    opacity="0.48"
  />


  <!-- =====================================================
       11. SWORD / DIAMOND CONTACT
  ====================================================== -->

  <path
    d="
      M627 898
      L634 914
      L627 930
      L620 914
      Z
    "
    fill="url(#mkcTip)"
    filter="url(#mkcGlow)"
  />

  <circle
    cx="627"
    cy="914"
    r="3"
    fill="#FFF9DE"
    opacity="0.96"
  />


  <!-- =====================================================
       12. FINAL ENERGY LIGHT
  ====================================================== -->

  <g filter="url(#mkcGlow)">

    <ellipse
      cx="627"
      cy="1127"
      rx="150"
      ry="3"
      fill="#318FFF"
      opacity="0.90"
    />

    <ellipse
      cx="627"
      cy="1127"
      rx="85"
      ry="2"
      fill="#E9F5FF"
      opacity="0.72"
    />

    <path
      d="
        M627 1099
        L633 1127
        L627 1170
        L621 1127
        Z
      "
      fill="url(#mkcStar)"
    />

    <circle
      cx="627"
      cy="1127"
      r="2.5"
      fill="#FFFFFF"
    />

  </g>

</svg>
`;


/**
 * ============================================================
 * REACT COMPONENT
 * ============================================================
 */

export default function MKCLogo({
  size = 300,
  width,
  height,
  className = "",
  style = {},
  variant = "default",
  glowIntensity = "low",
  showBackground = false,
}) {

  const rawId = useId();

  const safeId =
    rawId
      ? rawId.replace(/:/g, "")
      : "mkc";


  const primaryId =
    `mkcPrimary-${safeId}`;

  const brightId =
    `mkcBright-${safeId}`;

  const deepId =
    `mkcDeep-${safeId}`;

  const centerLightId =
    `mkcCenterLight-${safeId}`;

  const starId =
    `mkcStar-${safeId}`;

  const swordId =
    `mkcSword-${safeId}`;

  const tipId =
    `mkcTip-${safeId}`;

  const glowId =
    `mkcGlow-${safeId}`;

  const coreGlowId =
    `mkcCoreGlow-${safeId}`;


  const stdDev =
    glowIntensity === "high"
      ? 5
      : glowIntensity === "medium"
        ? 3
        : 2;


  const variantClass =
    variant !== "default"
      ? `mkc-logo-${variant}`
      : "";


  const finalWidth =
    width || size;

  const finalHeight =
    height || size;


  return (
    <div
      className={`
        inline-flex
        items-center
        justify-center
        mkc-logo-container
        ${variantClass}
        ${className}
      `}
      style={{
        width: finalWidth,
        height: finalHeight,
        ...style,
      }}
    >

      <svg
        viewBox="0 0 1254 1254"
        width="100%"
        height="100%"
        xmlns="http://www.w3.org/2000/svg"
        aria-label="Mastery Key Coach logo"
        role="img"
        preserveAspectRatio="xMidYMid meet"
      >

        <defs>

          <linearGradient
            id={primaryId}
            x1="0"
            y1="0"
            x2="1"
            y2="1"
          >
            <stop offset="0%" stopColor="#FFFFFF"/>
            <stop offset="8%" stopColor="#F9FCFF"/>
            <stop offset="20%" stopColor="#D9EBFF"/>
            <stop offset="34%" stopColor="#76BAFF"/>
            <stop offset="48%" stopColor="#278AF7"/>
            <stop offset="63%" stopColor="#1268DA"/>
            <stop offset="78%" stopColor="#0A499F"/>
            <stop offset="91%" stopColor="#063574"/>
            <stop offset="100%" stopColor="#02142F"/>
          </linearGradient>


          <linearGradient
            id={brightId}
            x1="0"
            y1="0"
            x2="1"
            y2="1"
          >
            <stop offset="0%" stopColor="#FFFFFF"/>
            <stop offset="14%" stopColor="#FFFFFF"/>
            <stop offset="30%" stopColor="#EFF7FF"/>
            <stop offset="47%" stopColor="#CAE3FF"/>
            <stop offset="63%" stopColor="#6CB2FF"/>
            <stop offset="80%" stopColor="#2A87EE"/>
            <stop offset="100%" stopColor="#0A54B8"/>
          </linearGradient>


          <linearGradient
            id={deepId}
            x1="0"
            y1="0"
            x2="0"
            y2="1"
          >
            <stop offset="0%" stopColor="#2F95FF"/>
            <stop offset="20%" stopColor="#146BDD"/>
            <stop offset="40%" stopColor="#0B4BA7"/>
            <stop offset="62%" stopColor="#063576"/>
            <stop offset="82%" stopColor="#031F4A"/>
            <stop offset="100%" stopColor="#010A20"/>
          </linearGradient>


          <linearGradient
            id={centerLightId}
            x1="0"
            y1="0"
            x2="0"
            y2="1"
          >
            <stop offset="0%" stopColor="#FFFFFF"/>
            <stop offset="20%" stopColor="#F5FAFF"/>
            <stop offset="42%" stopColor="#C4E1FF"/>
            <stop offset="61%" stopColor="#69B2FF"/>
            <stop offset="80%" stopColor="#1D77E8"/>
            <stop offset="100%" stopColor="#0A469D"/>
          </linearGradient>


          <radialGradient id={starId}>
            <stop offset="0%" stopColor="#FFFFFF"/>
            <stop offset="30%" stopColor="#FFFFFF"/>
            <stop offset="52%" stopColor="#EEF8FF"/>
            <stop offset="72%" stopColor="#A9D5FF"/>
            <stop offset="88%" stopColor="#58AAFF"/>
            <stop offset="100%" stopColor="#2177E7"/>
          </radialGradient>


          <linearGradient
            id={swordId}
            x1="0"
            y1="0"
            x2="1"
            y2="0"
          >
            <stop offset="0%" stopColor="#021532"/>
            <stop offset="18%" stopColor="#0A3B80"/>
            <stop offset="34%" stopColor="#1B77E5"/>
            <stop offset="46%" stopColor="#65AFFF"/>
            <stop offset="50%" stopColor="#FFFFFF"/>
            <stop offset="54%" stopColor="#69B3FF"/>
            <stop offset="66%" stopColor="#1A76E2"/>
            <stop offset="82%" stopColor="#0A3B80"/>
            <stop offset="100%" stopColor="#021532"/>
          </linearGradient>


          <linearGradient
            id={tipId}
            x1="0"
            y1="0"
            x2="0"
            y2="1"
          >
            <stop offset="0%" stopColor="#FFFFFF"/>
            <stop offset="38%" stopColor="#FFF8DE"/>
            <stop offset="68%" stopColor="#F0CA65"/>
            <stop offset="100%" stopColor="#AD7518"/>
          </linearGradient>


          <filter
            id={glowId}
            x="-35%"
            y="-35%"
            width="170%"
            height="170%"
          >

            <feGaussianBlur
              stdDeviation={stdDev}
              result="blur"
            />

            <feColorMatrix
              in="blur"
              type="matrix"
              values="
                0 0 0 0 0.03
                0 0 0 0 0.32
                0 0 0 0 0.95
                0 0 0 0.58 0
              "
              result="blueGlow"
            />

            <feMerge>
              <feMergeNode in="blueGlow"/>
              <feMergeNode in="SourceGraphic"/>
            </feMerge>

          </filter>


          <filter
            id={coreGlowId}
            x="-50%"
            y="-50%"
            width="200%"
            height="200%"
          >
            <feGaussianBlur stdDeviation="8"/>
          </filter>

        </defs>


        {showBackground && (
          <rect
            width="1254"
            height="1254"
            rx="60"
            fill="#020914"
          />
        )}


        {/* CENTER ATMOSPHERE */}

        <ellipse
          cx="627"
          cy="620"
          rx="285"
          ry="345"
          fill="#0E61D4"
          opacity="0.06"
          filter={`url(#${coreGlowId})`}
        />


        {/* 1. TOP DIAMOND */}

        <g
          transform="translate(75.24,20) scale(0.88,0.88)"
          filter={`url(#${glowId})`}
        >

          <path
            d="
              M627 42
              C591 94 550 130 505 158
              C550 183 588 215 609 252
              C619 270 624 286 627 306
              C630 286 635 270 645 252
              C666 215 704 183 749 158
              C704 130 663 94 627 42
              Z
            "
            fill="none"
            stroke={`url(#${primaryId})`}
            strokeWidth="19"
            strokeLinejoin="miter"
          />

          <path
            d="
              M627 104
              C623 132 613 148 584 157
              C613 163 623 174 627 210
              C631 174 641 163 670 157
              C641 148 631 132 627 104
              Z
            "
            fill={`url(#${starId})`}
          />

        </g>


        {/* 2. CROSSBAR */}

        <g filter={`url(#${glowId})`}>

          <path
            d="
              M375 261
              L568 261
              L565 286
              L405 286
              L414 300
              L567 328
              L394 307
              Z
            "
            fill={`url(#${primaryId})`}
          />

          <path
            d="
              M686 261
              L879 261
              L860 307
              L687 328
              L840 300
              L849 286
              L689 286
              Z
            "
            fill={`url(#${primaryId})`}
          />

          <path
            d="M388 268 L548 268"
            fill="none"
            stroke="#FFFFFF"
            strokeWidth="3"
            opacity="0.42"
            strokeLinecap="round"
          />

          <path
            d="M706 268 L866 268"
            fill="none"
            stroke="#FFFFFF"
            strokeWidth="3"
            opacity="0.42"
            strokeLinecap="round"
          />

        </g>


        {/* 3. ANCHOR */}

        <g
          transform="translate(62,-10) scale(0.90,1.025)"
          filter={`url(#${glowId})`}
        >

          <path
            d="
              M246 548
              C216 596 196 654 197 710
              C198 761 210 806 224 840
              C229 807 240 780 259 755
              C247 779 241 801 242 820
              C285 878 346 915 423 935
              C355 902 305 858 276 806
              C247 755 232 704 236 653
              C239 613 244 579 246 548
              Z
            "
            fill={`url(#${brightId})`}
          />

          <path
            d="
              M1004 548
              C1034 596 1054 654 1057 710
              C1056 761 1044 806 1030 840
              C1025 807 1014 780 995 755
              C1007 779 1013 801 1012 820
              C969 878 908 915 831 935
              C899 902 949 858 978 806
              C1007 755 1022 704 1018 653
              C1015 613 1010 579 1004 548
              Z
            "
            fill={`url(#${brightId})`}
          />

          <path
            d="
              M287 649
              C305 717 348 774 406 808
              C454 836 509 848 552 837
              C584 829 599 806 599 761
              L599 599
              L627 571
              L627 849
              C627 880 608 901 580 914
              C519 942 448 925 388 890
              C326 853 284 793 267 720
              C260 689 262 666 287 649
              Z
            "
            fill={`url(#${primaryId})`}
          />

          <path
            d="
              M963 649
              C945 717 902 774 844 808
              C796 836 741 848 702 837
              C670 829 655 806 655 761
              L655 599
              L627 571
              L627 849
              C627 880 646 901 674 914
              C731 942 802 925 862 890
              C924 853 966 793 983 720
              C990 689 988 666 963 649
              Z
            "
            fill={`url(#${primaryId})`}
          />

        </g>


        {/* OUTER SWEEP */}

        <g
          transform="translate(62,-5) scale(0.90,1.025)"
          fill="none"
          stroke={`url(#${primaryId})`}
          strokeLinecap="round"
          filter={`url(#${glowId})`}
        >

          <path
            d="
              M221 770
              C257 851 323 908 411 948
              C493 985 559 1006 627 1075
              C695 1006 759 985 839 948
              C927 908 993 851 1029 770
            "
            strokeWidth="19"
          />

          <path
            d="
              M246 810
              C291 879 348 919 425 950
              C503 981 567 1001 627 1058
              C687 1001 749 981 825 950
              C902 919 959 879 1004 810
            "
            strokeWidth="11"
          />

        </g>


        {/* 5. ONE CONTINUOUS CENTER SWORD */}

        <g filter={`url(#${glowId})`}>

          <path
            d="
              M600 240
              L610 205
              L627 182
              L644 205
              L654 240
              L654 478
              L646 505
              L646 888
              L627 925
              L608 888
              L608 505
              L600 478
              Z
            "
            fill={`url(#${swordId})`}
          />

          <path
            d="
              M627 205
              L638 239
              L638 482
              L637 505
              L637 882
              L627 905
              L617 882
              L617 505
              L616 482
              L616 239
              Z
            "
            fill={`url(#${centerLightId})`}
            opacity="0.88"
          />

          <path
            d="M627 205 L627 905"
            fill="none"
            stroke="#FFFFFF"
            strokeWidth="2.5"
            opacity="0.78"
            strokeLinecap="round"
          />

        </g>


        {/* 6. M + K — JOINED GROUP */}

        <g
          transform="translate(120,30) scale(0.86,0.94)"
          filter={`url(#${glowId})`}
          fill={`url(#${brightId})`}
        >

          {/* M */}

          <path
            d="
              M263 372
              L331 372
              L412 468
              L494 372
              L548 372
              L548 628
              L487 628
              L487 461
              L425 538
              L401 538
              L335 461
              L335 628
              L263 628
              Z
            "
          />

          {/* K */}

          <path
            d="
              M493 372
              L548 372
              L548 474
              L630 372
              L720 372
              L632 490
              L730 628
              L666 628
              L595 532
              L548 566
              L548 628
              L493 628
              Z
            "
          />

        </g>


        {/* 7. C — UNCHANGED */}

        <g
          transform="translate(83.91,30) scale(0.86,0.94)"
          filter={`url(#${glowId})`}
          fill={`url(#${brightId})`}
        >

          <path
            d="
              M960 372
              L960 430
              L850 430
              C815 430 796 448 796 482
              L796 522
              C796 556 815 574 850 574
              L960 574
              L960 628
              L834 628
              C766 628 730 590 730 522
              L730 478
              C730 410 766 372 834 372
              Z
            "
          />

        </g>


        {/* 8. M + K HIGHLIGHTS */}

        <g
          transform="translate(120,30) scale(0.86,0.94)"
          fill="none"
          stroke="#FFFFFF"
          strokeWidth="3"
          opacity="0.48"
          strokeLinecap="round"
        >

          <path
            d="
              M278 383
              L328 383
              L412 480
              L490 383
            "
          />

          <path
            d="
              M503 383
              L540 383
              L540 487
            "
          />

        </g>


        {/* 9. C HIGHLIGHT */}

        <g
          transform="translate(83.91,30) scale(0.86,0.94)"
          fill="none"
          stroke="#FFFFFF"
          strokeWidth="3"
          opacity="0.48"
          strokeLinecap="round"
        >

          <path
            d="
              M842 383
              L948 383
            "
          />

        </g>


        {/* 10. BOTTOM DIAMOND */}

        <path
          d="
            M627 905
            L678 959
            L627 1030
            L576 959
            Z
          "
          fill={`url(#${deepId})`}
          filter={`url(#${glowId})`}
        />

        <path
          d="
            M627 920
            L662 959
            L627 1008
            L592 959
            Z
          "
          fill="none"
          stroke="#5DAAFF"
          strokeWidth="3"
          opacity="0.48"
        />


        {/* 11. SWORD / DIAMOND CONTACT */}

        <path
          d="
            M627 898
            L634 914
            L627 930
            L620 914
            Z
          "
          fill={`url(#${tipId})`}
          filter={`url(#${glowId})`}
        />

        <circle
          cx="627"
          cy="914"
          r="3"
          fill="#FFF9DE"
          opacity="0.96"
        />


        {/* 12. FINAL ENERGY LIGHT */}

        <g filter={`url(#${glowId})`}>

          <ellipse
            cx="627"
            cy="1127"
            rx="150"
            ry="3"
            fill="#318FFF"
            opacity="0.90"
          />

          <ellipse
            cx="627"
            cy="1127"
            rx="85"
            ry="2"
            fill="#E9F5FF"
            opacity="0.72"
          />

          <path
            d="
              M627 1099
              L633 1127
              L627 1170
              L621 1127
              Z
            "
            fill={`url(#${starId})`}
          />

          <circle
            cx="627"
            cy="1127"
            r="2.5"
            fill="#FFFFFF"
          />

        </g>

      </svg>

    </div>
  );
}


export { MKCLogo as Logo };
