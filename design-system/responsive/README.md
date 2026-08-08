# Responsive

Policy: `codestrata-accessibility-responsive-policy:1.0` (Slice 14.11)  
Contract: `design-system/contracts/responsive.json`  
Rules: `design-system/responsive/rules.json`

| Breakpoint | px | Behavior |
| ---------- | -- | -------- |
| wrap | 1160 | Max content width |
| nav | 1040 | Collapse primary nav / open drawer |
| tablet | 960 | Stack multi-column sections |
| mobile | 720 | Single column; larger tap targets |

Rules:

1. No horizontal scroll on primary reading layouts at 320px+.
2. Hero type may scale down but keep Space Grotesk for H1.
3. Tables may scroll horizontally inside a contained panel.
4. Sticky header remains; scroll-padding accounts for header height.
