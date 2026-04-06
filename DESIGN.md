# Design System Specification: SUPER COMPTA

## 1. Overview & Creative North Star
**The Creative North Star: "The Moorish Vault"**

Moving beyond the cold, sterile nature of traditional fintech, this design system adopts a philosophy we call "The Moorish Vault." It combines the architectural precision of Andalusian geometry with the modern weight of a secure Swiss bank. 

The goal is to break the "SaaS template" look. Instead of a standard 12-column grid, we use **intentional asymmetry** and **tonal layering** to guide the eye. We replace aggressive structural lines with subtle shifts in depth, treating the interface like a series of nested courtyards. The "Super Compta" experience should feel like walking through a contemporary architectural marvel—spacious, premium, and inherently secure.

---

### 2. Colors: Tonal Depth & Signature Textures
Our palette rejects the "flat" trend in favor of professional depth. We use the contrast between Emerald and Navy to signify growth and stability, with Gold accents used exclusively for high-value interactions.

**The "No-Line" Rule:** 
Standard 1px borders are strictly prohibited for sectioning. To define boundaries, use background color shifts. For example, a `surface-container-low` component should sit on a `surface` background. The transition between colors provides a softer, more premium separation than a line ever could.

**Surface Hierarchy & Nesting:**
*   **Background (`#f8f9fa`):** The primary canvas.
*   **Surface-Container-Lowest (`#ffffff`):** Reserved for primary interactive cards to create a "pop" of clarity.
*   **Surface-Container-High (`#e7e8e9`):** Used for global navigation or utility sidebars to provide a grounded, structural feel.

**The Glass & Gradient Rule:**
To move beyond a generic fintech feel, floating elements (like modals or tooltips) must utilize **Glassmorphism**. 
*   Apply `surface` color at 80% opacity with a `20px` backdrop-blur. 
*   **Signature Texture:** Use a subtle linear gradient on primary CTAs from `primary` (`#004d34`) to `primary_container` (`#006747`) at a 135-degree angle. This adds "soul" and weight to the action.

---

### 3. Typography: The Editorial Scale
We use a high-contrast typography pairing to balance technical precision with premium character.

*   **Display & Headlines (Manrope):** The wider, geometric stance of Manrope provides an authoritative, editorial feel. Use `display-lg` for dashboard summaries to make financial data feel like a headline.
*   **Body & Labels (Inter):** Inter is used for all transactional data and micro-copy. Its high x-height ensures legibility in dense accounting tables.
*   **Gold Accents:** Use `tertiary` (`#573e00`) for `label-md` when highlighting positive financial trends or premium status indicators.

---

### 4. Elevation & Depth: Tonal Layering
Depth in this system is a result of "stacking" light and shadow, not drawing boxes.

*   **The Layering Principle:** Instead of shadows, use "Surface Tiers." Place a `surface-container-lowest` card on a `surface-container-low` section. This creates a natural, soft lift.
*   **Ambient Shadows:** For floating elements (Modals/Dropdowns), use an "Ambient Shadow": `0 12px 32px -4px rgba(25, 28, 29, 0.06)`. Note the low 6% opacity—it should feel like a soft glow, not a hard drop.
*   **The "Ghost Border" Fallback:** If a border is required for accessibility, use the `outline_variant` (`#bec9c1`) at **15% opacity**. This creates a suggestion of a boundary without cluttering the UI.
*   **Zellige Motifs:** Incorporate the Moroccan aesthetic through **vector masks**. Apply a geometric zellige pattern as a subtle `0.05` opacity overlay on `primary` containers or as a ghosted watermark in the bottom-right corner of large data cards.

---

### 5. Components: Modern Financial Primitives

*   **Buttons:**
    *   *Primary:* Solid Emerald (`primary`) with a subtle Gold (`tertiary_fixed`) glow on hover. Border-radius: `sm` (`0.125rem`) for a sharp, professional look.
    *   *Secondary:* Navy (`secondary`) background with `on_secondary` text. No border.
*   **Input Fields:**
    *   Use `surface_container_lowest` for the field background. 
    *   On focus, do not use a heavy border; use a 2px bottom-accent in Gold (`tertiary`) and a subtle `surface_tint` glow.
*   **Data Cards:** 
    *   **Strictly no dividers.** Use `body-sm` labels in `on_surface_variant` to categorize data, and use vertical white space (from the `xl` spacing scale) to separate groups.
*   **The "Pattern Border":** 
    *   For featured sections, replace a top-border with a 4px tall strip of a geometric Moroccan pattern in `primary` and `tertiary` tones.
*   **Footer:** 
    *   A clean, wide-spaced footer using `surface_container_highest`. 
    *   Text: "Conçu par Faisal Karmi" (Styled in `label-sm`, uppercase, with `0.1em` letter spacing).

---

### 6. Do’s and Don’ts

**Do:**
*   **Use Asymmetry:** Place a large `display-md` balance on the left and a smaller, glassmorphic "Recent Activity" card slightly overlapping it on the right.
*   **Embrace Breathing Room:** Use the `xl` (0.75rem) and higher spacing tokens. High-end design requires space to "breathe."
*   **Tonal Transitions:** Transition from `background` to `surface_container` to indicate a shift from global navigation to specific content.

**Don’t:**
*   **Don't use 100% Black:** Always use `on_surface` (`#191c1d`) for text to maintain a soft, premium feel.
*   **Don't use Rounded Corners for everything:** Stick to `sm` (2px) or `md` (6px) for cards. Avoid `full` rounding except for small tags/chips. We want the app to feel "robust," not "bubbly."
*   **Don't clutter with patterns:** Zellige motifs should be treated like a spice—used sparingly in backgrounds or header accents, never as a dominant foreground element.