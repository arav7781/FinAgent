# QuantumFleet AI — Seed Round

*Synthetic pitch deck. Every figure is invented for testing the document
ingestion path. Convert to PDF to exercise Docling:*
`pandoc dataset/sample_pitch_deck.md -o sample_pitch_deck.pdf`

---

## The problem

Mid-size freight operators in India run 40 to 300 trucks. For that segment,
roughly 28% of distance travelled is empty — a truck returning from a delivery
with no load. Large fleets solve this with in-house planning teams. Operators
below about 300 trucks cannot justify the headcount, so dispatch is done over
phone calls and a whiteboard.

Every empty kilometre is fuel, driver hours, and vehicle wear against no
revenue. At current diesel prices an operator running 120 trucks loses an
estimated ₹1.4 crore a year to empty running.

## The product

QuantumFleet re-plans loads continuously rather than once per morning. Three
inputs: live vehicle position, the open order book, and road conditions. The
planner proposes reassignments to the dispatcher, who accepts or rejects them.

We deliberately kept a human in the loop. Dispatchers know things the system
does not — which driver is nearing hours, which customer tolerates a late
delivery — and a planner that overrides them gets switched off in a week.

## Traction

| Metric | Value |
| :--- | :--- |
| Paying pilots | 4 |
| Trucks under management | 310 |
| MRR | $9,000 |
| Month-on-month growth | 11% |
| Empty-mile reduction (pilot average) | 19% |
| Logo retention since launch | 4 of 4 |

The 19% figure is measured against each operator's own baseline in the eight
weeks before deployment, not against an industry average.

## Business model

Per-truck SaaS at ₹2,400 per truck per month, billed annually. Gross margin is
81% after cloud and map-data costs. Payback on customer acquisition is 7 months
at current pricing.

## Market

- **TAM** — ₹8,400 crore: all mid-size freight operators in India.
- **SAM** — ₹2,500 crore: operators with 40+ trucks and an existing GPS system.
- **SOM** — ₹180 crore: our three target states over five years.

## Competition

| | QuantumFleet | Incumbent TMS | In-house planning |
| :--- | :--- | :--- | :--- |
| Setup time | 2 weeks | 4-6 months | n/a |
| Cost per truck / month | ₹2,400 | ₹6,000+ | Salary cost |
| Live re-planning | Yes | Batch, overnight | Manual |
| Target fleet size | 40-300 | 500+ | 300+ |

Incumbent transport management systems are built for large fleets and priced
accordingly. Our wedge is the segment they do not serve profitably.

## Team

- **Arjun Malhotra**, CEO — six years in supply chain at Flipkart, led the
  last-mile routing team.
- **Dr. Elena Novak**, CTO — PhD in operations research; built the optimisation
  engine at a European logistics firm.
- **Ravi Krishnan**, Head of Operations — ran a 200-truck regional fleet for six
  years. Our first three customers came through his network.

Six people total. We have no full-time sales hire; the founders sell.

## The ask

Raising **$500,000** at a $4M cap, to cover 18 months:

- 45% engineering (three hires)
- 30% sales and customer success (first commercial hire)
- 15% infrastructure and map data
- 10% working capital

**Milestone:** 25 paying operators and $60k MRR by month 18.

## Known risks

We would rather state these than have you find them.

1. **Customer concentration** — one pilot is 38% of current revenue.
2. **No commercial hire** — founder-led sales has worked to four customers. It
   is not proven past that, and it is the first thing we spend the round on.
3. **Data dependency** — we rely on a third-party map provider whose pricing
   has risen twice in two years.
4. **Incumbent response** — nothing stops a large TMS vendor from launching a
   cut-down tier. Our defence is setup time and segment focus, not technology.
