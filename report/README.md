# report/

[**FinAgent_Report.pdf**](FinAgent_Report.pdf) — the project report. 21 pages,
seven diagrams.

| Section | Covers |
| :--- | :--- |
| 1. Statement of Need | Why early-stage diligence is expensive, why a chatbot is not the fix, and the seven requirements that follow. |
| 2. Technical Functionality | Both pipelines node by node, and the design decision inside each. |
| 3. Architecture | Layering, module layout, request path, configuration, deployment, state. |
| 4. Usage and Scope | Installation, both workflows in practice, testing, and what is deliberately out of scope. |
| 5. Impact Overview | What changes for each user, limitations, ethical considerations, further work. |
| 6. Appendix | Technology stack, full API surface, environment variables, commands, fixtures. |

## Rebuilding it

```bash
make report
```

This re-renders every diagram from
[`docs/diagrams/generate_diagrams.py`](../docs/diagrams/generate_diagrams.py)
and then rebuilds the PDF, so no figure can drift from the code it describes.

| File | Role |
| :--- | :--- |
| [`docs/report/content.py`](../docs/report/content.py) | The writing. Edit here. |
| [`docs/report/build_report.py`](../docs/report/build_report.py) | The renderer — styles, page furniture, figure captions. |
