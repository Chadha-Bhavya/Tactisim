## 🎯 Overview

**TactiSim** turns football tactics into data-driven decisions.  
Given a match snapshot (11v11 positions, ball location, match context), it generates optimized defensive adjustments using beam search and weighted tactical models.

**Status:** ✅ Backend complete · 🚧 Frontend in progress

---

## ✨ Features

### Backend (Complete)
- Beam search evaluating 100+ defensive formations per query
- Weighted scoring using compactness, press access, line height risk, ball-side shift
- Context-aware weights (protect lead vs high press)
- Hard constraints for movement, spacing, pitch bounds, goalkeeper zone
- Coordinate outputs with tactical reasoning

### Frontend (In Development)
- Interactive pitch with drag and drop player placement (React-Konva)
- Real-time visualization of defensive adjustments
- Global state with Zustand, API sync with TanStack Query
- Responsive styling with Tailwind CSS

---

## 🙏 Acknowledgments

Inspired by modern tactical ideas from Pep Guardiola, Jürgen Klopp, and Thomas Tuchel ⚽

---

## 📧 Contact

**Bhavya Chadha**  
https://github.com/Chadha-Bhavya/tactisim
