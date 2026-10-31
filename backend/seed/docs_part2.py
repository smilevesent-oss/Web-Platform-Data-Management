# Seed documents, part 2: Engineering & Architecture, Operations & SOPs.

DOCS = [
    {
        "title": "Architecture Decision Record: Moving from Monolith to Modular Services",
        "category": "engineering",
        "doc_type": "Decision Record",
        "department": "Engineering",
        "tags": ["Architecture", "Microservices", "Decision Record"],
        "summary": "Records why the order platform will be split into a small number of modular services rather than dozens of microservices, and the migration plan.",
        "content": """Context: The order management platform is a single application with roughly 400,000 lines of code deployed as one unit. Release frequency has fallen to once every two weeks because any change requires a full regression test, and three teams regularly block each other during deployments.

Options considered: keeping the monolith and improving test automation; splitting it into many fine-grained microservices; or extracting a small number of modular services along clear business boundaries.

Decision: We will extract four services aligned to business capabilities: catalogue, pricing, orders and fulfilment. Each will own its database schema. Communication between services will use asynchronous events for state changes and synchronous HTTP only for queries that need an immediate answer.

We rejected fine-grained microservices because the team does not yet have the operational maturity, such as distributed tracing and automated contract testing, that dozens of services would require. We may split services further later if a clear need appears.

Consequences: Teams will deploy independently, but we accept added complexity in data consistency. Reports that join data across services will move to the analytics warehouse. The migration will follow the strangler pattern, starting with pricing because it has the fewest dependencies.""",
    },
    {
        "title": "API Design Guidelines for RESTful Services",
        "category": "engineering",
        "doc_type": "Standard",
        "department": "Engineering",
        "tags": ["API", "REST", "Coding Standards"],
        "summary": "Conventions for resource naming, HTTP methods, status codes, pagination, error format and versioning that every internal and public API must follow.",
        "content": """Consistent APIs are easier to learn, document and integrate. These guidelines apply to every new HTTP API and to breaking changes in existing ones.

Resources are named with plural nouns in lower-case kebab-case, for example /purchase-orders/123/line-items. Verbs in paths are avoided; the HTTP method expresses the action. GET reads, POST creates, PUT replaces, PATCH partially updates and DELETE removes. GET requests must never change state.

Use status codes precisely: 200 for successful reads, 201 with a Location header for creation, 204 for successful requests with no body, 400 for malformed input, 401 when authentication is missing, 403 when the caller lacks permission, 404 when the resource does not exist, 409 for conflicts and 422 for validation errors.

Collections are paginated by default. Responses include the items, the total count and the page parameters, and the maximum page size is 100. Filtering uses query parameters named after the field being filtered.

Errors use a single JSON format containing a machine-readable code, a human-readable message and, for validation errors, a list of field-level problems. Breaking changes require a new major version in the URL path, and the previous version is supported for at least six months after the new one is released.""",
    },
    {
        "title": "Code Review Standards and Pull Request Etiquette",
        "category": "engineering",
        "doc_type": "Guide",
        "department": "Engineering",
        "tags": ["Code Review", "Coding Standards", "Collaboration"],
        "summary": "What reviewers should look for, how authors should prepare small reviewable changes and how to give feedback that is direct but respectful.",
        "content": """Code review exists to catch defects, share knowledge and keep the codebase consistent. It is not a gate for asserting personal preferences.

Authors should keep pull requests small, ideally under 400 changed lines. The description explains why the change is needed, how it was tested and anything the reviewer should pay special attention to. Unrelated refactoring belongs in a separate pull request.

Reviewers should focus first on correctness, security and data integrity, then on design and readability. Style issues that a formatter or linter could catch should be fixed by tooling, not by comments. Reviewers should respond within one working day; if a review will take longer, say so.

Comments should be specific and explain the reason. Prefix optional suggestions with 'nit' so the author knows they are not blocking. Ask questions rather than issue commands when the intent is unclear, for example 'What happens if this list is empty?'

Approval means the reviewer would be comfortable maintaining the code. Changes touching authentication, payments or personal data require a second reviewer from the owning team. Authors merge their own pull requests after approval and are responsible for monitoring the deployment.""",
    },
    {
        "title": "Database Migration Runbook for PostgreSQL",
        "category": "engineering",
        "doc_type": "Runbook",
        "department": "Platform Engineering",
        "tags": ["PostgreSQL", "Database", "Runbook"],
        "summary": "Safe procedure for schema changes on production PostgreSQL: expand-and-contract migrations, lock timeouts, index creation and rollback.",
        "content": """Schema changes on production databases must not cause downtime. We use the expand-and-contract pattern: first add new structures in a backwards-compatible way, then migrate code and data, and only then remove the old structures in a later release.

Every migration session must set a lock timeout, typically two seconds, so that a migration waiting for a lock fails quickly instead of blocking all traffic behind it. Statements that fail on the timeout can be retried during a quieter period.

Indexes on large tables are created with CREATE INDEX CONCURRENTLY, which does not block writes. This statement cannot run inside a transaction, so it must be placed in its own migration file. If it fails, the invalid index must be dropped before retrying.

Adding a column with a constant default is safe in recent PostgreSQL versions. Adding a NOT NULL constraint to an existing column is done in two steps: add a CHECK constraint marked NOT VALID, then validate it separately, which avoids a long exclusive lock.

Large data backfills run in batches of a few thousand rows with a short pause between batches, and progress is logged. Every migration must include a tested rollback or a written explanation of why rollback is not possible.""",
    },
    {
        "title": "Observability Standard: Logs, Metrics and Traces",
        "category": "engineering",
        "doc_type": "Standard",
        "department": "Platform Engineering",
        "tags": ["Observability", "Monitoring", "Infrastructure"],
        "summary": "Minimum telemetry each service must emit, structured logging rules, the four golden signals and alerting principles that reduce pager fatigue.",
        "content": """Every production service must emit structured logs, metrics and distributed traces through the shared telemetry library. This allows on-call engineers to investigate problems in any service using the same tools.

Logs are written as JSON with a timestamp, level, service name, trace identifier and message. Personal data such as e-mail addresses and payment details must never be logged. Debug logging is disabled in production by default and can be enabled temporarily for a single service.

Each service exposes the four golden signals: request rate, error rate, latency distribution and saturation of its key resources. Latency is reported as percentiles, at least the 50th, 95th and 99th, because averages hide the experience of the slowest users.

Traces propagate context across HTTP calls and message queues so that a single request can be followed through every service it touches. Sampling keeps all traces that contain errors and a percentage of successful ones.

Alerts must be actionable. Page a human only when users are affected or about to be, and base alerts on service level objectives rather than raw resource thresholds. Every alert links to a runbook explaining the first steps to take.""",
    },
    {
        "title": "Kubernetes Deployment Checklist",
        "category": "engineering",
        "doc_type": "Checklist",
        "department": "Platform Engineering",
        "tags": ["Kubernetes", "Infrastructure", "Deployment"],
        "summary": "Pre-production checklist for services on the shared Kubernetes cluster: resource requests, probes, disruption budgets, secrets and rollout strategy.",
        "content": """Before a service is deployed to the production cluster for the first time, the owning team must confirm each item in this checklist during a short review with the platform team.

Resource requests and limits are set for CPU and memory based on load-test measurements, not guesses. Memory limits should be close to requests to avoid nodes being overcommitted.

Liveness and readiness probes are configured separately. The readiness probe checks that the service can serve traffic, including connectivity to its dependencies; the liveness probe only checks that the process is not stuck, so that a database outage does not cause endless restarts.

At least two replicas run in different availability zones, and a PodDisruptionBudget ensures that node maintenance never removes all replicas at once.

Secrets are injected from the secrets vault and never baked into container images. Images are built from the approved base images and pass vulnerability scanning before promotion.

Rollouts use a rolling update with a maximum unavailable of zero, so capacity is never reduced during deployment. Services handling payments use canary releases with automatic rollback when error rates rise.""",
    },
    {
        "title": "Technical Debt Register: Q3 2026 Review",
        "category": "engineering",
        "doc_type": "Report",
        "department": "Engineering",
        "tags": ["Technical Debt", "Architecture", "Planning"],
        "summary": "Quarterly review of the top technical debt items, their estimated cost of delay and the remediation work scheduled for the next two quarters.",
        "content": """This review covers the twenty highest-ranked items in the technical debt register. Items are scored on two axes: the ongoing cost they impose on delivery and the risk they create for reliability or security.

The highest-scoring item remains the legacy authentication module in the customer portal. It uses an outdated session library, lacks support for passkeys and is understood by only two engineers. Replacing it is scheduled for Q4 and has been funded as a dedicated project.

Second is the nightly batch job that reconciles inventory between the warehouse system and the online store. It frequently overruns its window, causing stale stock levels in the morning. The team will replace it with event-driven updates, which also removes a manual correction step performed by operations staff.

Flaky end-to-end tests are the third item. Around eight percent of pipeline runs fail for reasons unrelated to the change being tested, which erodes trust in the test suite. A working group will quarantine unstable tests and rewrite the worst offenders as contract tests.

Overall, the share of engineering capacity spent on debt reduction was 17 percent this quarter, slightly below the 20 percent target agreed with product leadership.""",
    },
    {
        "title": "Incident Postmortem: Checkout Latency Spike on 14 August",
        "category": "engineering",
        "doc_type": "Postmortem",
        "department": "Platform Engineering",
        "tags": ["Postmortem", "Incident Response", "PostgreSQL"],
        "summary": "Blameless review of a 47-minute degradation of checkout caused by a missing index after a schema migration, with timeline and follow-up actions.",
        "content": """Summary: For 47 minutes, checkout requests experienced a 95th-percentile latency above eight seconds, and about 12 percent of attempts timed out. No data was lost, but an estimated 1,900 orders were abandoned.

Root cause: A migration released that morning rewrote the order lines table to add a new column. The migration recreated the table but did not recreate a composite index used by the checkout query. Under normal morning traffic the query was still fast enough, but at the lunchtime peak the resulting sequential scans saturated database CPU.

Detection: The latency alert fired eleven minutes after the degradation began. The delay occurred because the alert evaluated a 10-minute average rather than a percentile over a shorter window.

Resolution: The on-call engineer identified the slow query from the database's statement statistics and created the missing index concurrently. Latency returned to normal four minutes after the index was built.

Actions: Add an automated check that compares indexes before and after each migration in staging. Change the checkout latency alert to use the 95th percentile over five minutes. Add a section on index verification to the database migration runbook. All three actions have owners and are due within thirty days.""",
    },
    {
        "title": "Customer Support Ticket Triage SOP",
        "category": "operations",
        "doc_type": "SOP",
        "department": "Customer Operations",
        "tags": ["Customer Support", "SLA", "Process"],
        "summary": "Standard operating procedure for classifying incoming tickets by priority, routing them to the right queue and meeting first-response targets.",
        "content": """All customer requests arrive in the unified support inbox, whether by e-mail, web form or chat. The triage agent on shift reviews new tickets every fifteen minutes during business hours.

Each ticket is assigned a priority. Urgent covers outages, security concerns and payment failures affecting many customers. High covers problems that block a single customer's work. Normal covers questions and non-blocking issues. Low covers feature requests and general feedback.

First-response targets are 30 minutes for Urgent, two hours for High, eight business hours for Normal and two business days for Low. Urgent tickets also trigger a message in the incident channel so that engineering is aware.

Tickets are routed by product area using tags. Billing questions go to the finance support queue, account access issues to the identity queue and technical faults to the product support queue. When the category is unclear, the ticket stays with the triage agent, who contacts the customer for more detail.

Before closing a ticket, agents confirm with the customer that the issue is resolved and link any related knowledge base article. Tickets reopened within seven days are reviewed weekly to identify gaps in the knowledge base.""",
    },
    {
        "title": "Business Continuity Plan: Head Office",
        "category": "operations",
        "doc_type": "Plan",
        "department": "Operations",
        "tags": ["Business Continuity", "Risk Management", "Disaster Recovery"],
        "summary": "Critical processes, recovery time objectives and the activation procedure if the head office becomes unavailable due to fire, flood or power loss.",
        "content": """This plan describes how Meridian Group will keep critical processes running if the head office becomes unavailable. It is tested twice a year through a tabletop exercise and once a year through a live failover of key systems.

Critical processes and their recovery time objectives are: customer order processing within four hours, payroll within two days, customer support within four hours and financial close within five days. Other processes can be suspended for up to two weeks.

Because most staff can work remotely, the main recovery strategy is to move critical teams to home working. A small number of roles that require physical equipment, such as the mailroom and the cheque processing team, will relocate to the regional office, which keeps twenty reserved workstations.

The plan is activated by any member of the crisis management team, which includes the Chief Operating Officer, the head of IT and the head of facilities. Activation triggers an alert to all staff through the emergency notification system, followed by instructions on the intranet status page.

Each department maintains a contact tree and keeps printed copies of essential procedures off site. Department heads must review their section of this plan every six months.""",
    },
    {
        "title": "IT Asset Lifecycle and Laptop Refresh Procedure",
        "category": "operations",
        "doc_type": "Procedure",
        "department": "IT Services",
        "tags": ["IT Access", "Asset Management", "Process"],
        "summary": "How laptops and other IT assets are requested, registered, refreshed every four years and securely wiped before disposal or donation.",
        "content": """Every laptop, monitor and mobile device purchased by the company is registered in the asset inventory with its serial number, owner and purchase date. Devices are enrolled in device management before being handed to employees.

Standard laptops are refreshed every four years, or earlier if the device fails a hardware diagnostic and repair is not economical. Engineering and design roles may request a higher-specification model with manager approval.

Refresh notifications are sent automatically one month before the device reaches its refresh date. The employee books a swap appointment; data is synchronised from cloud storage, so local files are not migrated except in documented exceptions.

When a device is returned, IT performs a cryptographic erase and verifies it in the management console before the device leaves company custody. Devices that cannot be erased because of hardware failure have their storage physically destroyed by a certified contractor, who provides a certificate of destruction.

Devices in good condition may be donated to registered charities or sold to employees at a fixed residual price. Lost or stolen devices must be reported within 24 hours so they can be remotely locked and wiped.""",
    },
    {
        "title": "Travel and Expense Reimbursement Procedure",
        "category": "operations",
        "doc_type": "Procedure",
        "department": "Finance",
        "tags": ["Expenses", "Travel", "Finance"],
        "summary": "Booking rules for flights and hotels, daily meal limits, receipt requirements and the timeline for submitting and approving expense claims.",
        "content": """Business travel must be booked through the corporate travel platform, which applies negotiated rates and allows the company to locate travellers in an emergency. Bookings made elsewhere are reimbursed only if they are cheaper and the reason is documented.

Economy class is standard for flights under six hours. Premium economy may be booked for longer flights, and business class only with approval from an executive committee member. Hotels should fall within the city rate cap listed on the travel platform.

Meals are reimbursed at actual cost up to the daily limit for the destination. Alcohol is not reimbursed except at approved client entertainment events, which require the attendee names and the business purpose to be recorded.

Claims are submitted in the expense application within 30 days of the expense, with an itemised receipt photographed in the app. Expenses without receipts are reimbursed only up to a small threshold and only with a written explanation.

Managers approve claims within five working days. Finance audits a random sample each month, and repeated policy breaches are reported to the employee's department head.""",
    },
    {
        "title": "Office Health and Safety Induction",
        "category": "operations",
        "doc_type": "Guide",
        "department": "Facilities",
        "tags": ["Health and Safety", "Onboarding", "Facilities"],
        "summary": "Fire evacuation routes, first aid arrangements, workstation ergonomics and how to report hazards and near misses in company offices.",
        "content": """This induction must be completed by every employee and long-term contractor before working in a company office.

When the fire alarm sounds, leave the building immediately by the nearest marked exit and go to the assembly point shown on the floor plan by each lift. Do not use lifts and do not return for belongings. Fire wardens, identified by orange vests, will check each floor and report to the evacuation coordinator.

Each floor has at least two trained first aiders, whose names are displayed next to the first aid kit. Automated external defibrillators are located at reception and in the main kitchen.

A comfortable workstation reduces the risk of back, neck and wrist problems. The top of the monitor should be at or slightly below eye level, feet should rest flat on the floor and forearms should be roughly horizontal when typing. Employees can book an ergonomic assessment through the facilities portal.

Hazards such as trailing cables, spills or broken furniture should be reported through the facilities portal immediately. Near misses, where something could have caused an injury but did not, should also be reported, as they help prevent future accidents.""",
    },
    {
        "title": "Change Management Procedure for Production Systems",
        "category": "operations",
        "doc_type": "Procedure",
        "department": "IT Services",
        "tags": ["Change Management", "ITIL", "Deployment"],
        "summary": "Defines standard, normal and emergency changes, the change advisory board schedule and the records required for audit.",
        "content": """All changes to production systems must be recorded so that the company can understand what changed when an incident occurs and can demonstrate control to auditors.

Standard changes are low-risk, repeatable and pre-approved, such as deploying an application through the automated pipeline with passing tests. They are logged automatically by the pipeline and need no further approval.

Normal changes carry more risk, such as network reconfiguration or a database engine upgrade. They require a change request describing the purpose, risk, testing performed, implementation steps and rollback plan. The change advisory board reviews normal changes twice a week.

Emergency changes are made to restore service or close an actively exploited vulnerability. They may be implemented with the approval of the on-call manager and must be documented retrospectively within one working day.

A change freeze applies during the last week of the financial year and during major sales events. Only emergency changes are permitted during a freeze. Change success rates are reported monthly, and any change that caused an incident is reviewed at the next board meeting.""",
    },
    {
        "title": "Records Retention Schedule",
        "category": "operations",
        "doc_type": "Schedule",
        "department": "Legal",
        "tags": ["Records Management", "Compliance", "Data Protection"],
        "summary": "Minimum and maximum retention periods for common record types, including financial, HR, contract and customer records, and the disposal process.",
        "content": """Records must be kept long enough to meet legal, regulatory and business needs, and no longer. Keeping personal data longer than necessary breaches data protection law and increases the impact of any security incident.

Financial records, including invoices, ledgers and tax filings, are retained for ten years after the end of the financial year to which they relate.

Employee personnel files are retained for six years after employment ends. Recruitment records for unsuccessful candidates are retained for six months after the position is filled, unless the candidate agrees to be kept on file for future roles.

Contracts are retained for seven years after expiry or termination. Contracts executed as deeds are retained for thirteen years.

Customer account data is retained for as long as the account is active and for three years after closure, to handle disputes and refunds. Marketing consent records are kept for as long as the consent is relied upon, plus two years.

At the end of each retention period, records are deleted or destroyed securely. Legal holds suspend deletion for records relevant to litigation or investigations; system owners are notified when a hold is placed or released.""",
    },
]
