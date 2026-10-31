# Seed documents, part 4: Research & Market Insights, Product & Customer Experience.

DOCS = [
    {
        "title": "Southeast Asia E-Commerce Logistics Market Outlook 2026",
        "category": "research",
        "doc_type": "Research Report",
        "department": "Strategy & Insights",
        "tags": ["Market Research", "Logistics", "Southeast Asia"],
        "summary": "Analysis of last-mile delivery growth, cost pressures and consolidation trends across six Southeast Asian markets, with implications for our fulfilment strategy.",
        "content": """E-commerce parcel volumes in Southeast Asia continued to grow in 2025, driven by social commerce and the expansion of online grocery. Growth was strongest in Vietnam and the Philippines, where online penetration is still well below that of Singapore and Malaysia.

Last-mile delivery remains the largest cost component, accounting for around half of total logistics cost per parcel. Dense urban areas such as Ho Chi Minh City, Jakarta and Manila benefit from high drop density, while deliveries outside major cities cost two to three times more per parcel.

The market is consolidating. Several regional carriers merged or exited during the year, and marketplace-owned logistics arms now handle the majority of parcels in some countries. This reduces choice for independent merchants but has improved delivery reliability.

Customers increasingly expect same-day or next-day delivery in major cities, and cash on delivery remains common despite rapid growth in e-wallets. Failed first delivery attempts are a significant hidden cost, particularly for cash on delivery orders.

Implications for Meridian Group: we recommend expanding the use of parcel lockers and partner pick-up points in our three largest cities, piloting dynamic delivery slots to reduce failed attempts and renegotiating carrier contracts to include performance-based pricing.""",
    },
    {
        "title": "Customer Churn Analysis: Subscription Product Line",
        "category": "research",
        "doc_type": "Analysis",
        "department": "Data & Analytics",
        "tags": ["Churn", "Data Analysis", "Customer Retention"],
        "summary": "Survival analysis of 18 months of subscriber data identifying the main drivers of churn and the early warning signals that predict cancellation.",
        "content": """We analysed eighteen months of subscription data covering all customers who started a paid plan during the period. Monthly churn averaged 4.1 percent, but the rate was far from constant over a customer's lifetime.

Churn is concentrated early. Almost 40 percent of all cancellations occur within the first three months. Customers who reach month six churn at less than half the rate of new customers, which suggests that onboarding has a disproportionate effect on retention.

The strongest predictor of churn is low product usage in the first 14 days. Customers who complete at least three core actions in their first two weeks are 2.7 times more likely to still be subscribed after a year. Failed payments are the second largest driver; roughly one fifth of cancellations are involuntary and follow an expired or declined card.

Customers who contacted support and had their issue resolved on first contact churned less than customers who never contacted support at all. Unresolved tickets, however, more than doubled the churn risk in the following month.

Recommendations include a guided onboarding sequence focused on the three core actions, smarter payment retry logic with card updater services, and an early warning dashboard that flags accounts with declining usage for proactive outreach.""",
    },
    {
        "title": "Competitive Landscape: Document Management Software",
        "category": "research",
        "doc_type": "Research Report",
        "department": "Strategy & Insights",
        "tags": ["Competitive Analysis", "Market Research", "Software"],
        "summary": "Comparison of five document management platforms on search quality, permissions, integrations and pricing to inform our build-versus-buy decision.",
        "content": """We evaluated five document management platforms against the requirements gathered from legal, engineering and operations teams. The evaluation focused on search quality, permission granularity, integrations with our existing tools, administrative effort and total cost over five years.

Search quality varied more than expected. The two leading platforms offered full-text search with relevance ranking, filters by metadata and highlighting of matching passages. Others relied on simple keyword matching, which performed poorly for longer policy documents where the query terms appear many times in unrelated sections.

Permission models ranged from simple folder-level access to attribute-based rules. Our legal team requires document-level permissions with audit trails, which only three of the five platforms support without custom development.

All platforms provide connectors for common office suites, but only two support our identity provider for automatic provisioning and deprovisioning of users.

Building our own repository would cost more in the first two years but gives us full control over search ranking and analytics, which matters for our longer-term plan to improve findability using click data. We recommend a phased in-house build, starting with the core repository and basic search, then adding ranked retrieval.""",
    },
    {
        "title": "Employee Engagement Survey Results 2026",
        "category": "research",
        "doc_type": "Survey Report",
        "department": "People & Culture",
        "tags": ["Employee Wellbeing", "Survey", "Data Analysis"],
        "summary": "Results of the annual engagement survey: participation, engagement index by department, strongest and weakest themes, and the agreed action plan.",
        "content": """The 2026 engagement survey received responses from 84 percent of employees, up from 78 percent last year. The overall engagement index rose two points to 71, which is slightly above the benchmark for companies of similar size in our industry.

The highest-scoring themes were relationships with colleagues, belief in the company's mission and flexibility to balance work and personal life. Comments frequently mentioned the hybrid work policy as a reason for staying with the company.

The lowest-scoring themes were career growth and cross-team communication. Many respondents said they did not know what opportunities exist outside their own team or how promotion decisions are made. Several commented that important decisions are sometimes announced without explanation.

Engineering and customer operations recorded the largest improvements. Finance saw a decline of four points, which leadership attributes to the heavy workload during the new system implementation.

The action plan focuses on three commitments: publishing clear career frameworks for every job family by the end of Q1, launching an internal mobility board that lists open roles before they are advertised externally, and holding a monthly all-hands session where leaders explain the reasoning behind major decisions.""",
    },
    {
        "title": "Evaluating Search Relevance: Metrics and Methodology",
        "category": "research",
        "doc_type": "Research Note",
        "department": "Data & Analytics",
        "tags": ["Information Retrieval", "Search", "Data Analysis"],
        "summary": "How we will measure the quality of internal search: precision, recall, MRR and nDCG, building judgement sets, and using click logs as implicit feedback.",
        "content": """As we prepare to replace keyword matching in the document repository with ranked retrieval, we need a reliable way to measure whether search results are getting better.

Offline evaluation uses a fixed set of queries with human relevance judgements. For each query, assessors grade the top results as highly relevant, partially relevant or not relevant. From these judgements we compute precision at ten, mean reciprocal rank, which rewards placing the first relevant result near the top, and normalised discounted cumulative gain, which accounts for graded relevance and position.

Building the judgement set starts with real queries from the search log. We sample frequent queries, a selection of rare queries and queries that returned no results, because each group exposes different weaknesses.

Online evaluation uses implicit feedback from click logs. Useful signals include click-through rate on the first page, the position of the first click, the share of searches with no click and whether users reformulate their query. Clicks are biased towards higher positions, so comparisons between ranking methods should use interleaving or position-bias correction.

We recommend establishing a baseline with the current keyword search before introducing TF-IDF or BM25 ranking, so that improvements can be measured rather than assumed.""",
    },
    {
        "title": "TF-IDF and BM25: A Primer for the Search Team",
        "category": "research",
        "doc_type": "Research Note",
        "department": "Data & Analytics",
        "tags": ["Information Retrieval", "Search", "BM25"],
        "summary": "Explains term frequency, inverse document frequency, document length normalisation and the BM25 parameters k1 and b, with guidance on tokenisation.",
        "content": """Ranked retrieval assigns each document a score for a query and returns documents in order of score. Two classic scoring functions, TF-IDF and BM25, remain strong baselines and are the starting point for our repository search.

Term frequency measures how often a query term appears in a document. A document that mentions 'retention' ten times is more likely to be about retention than one that mentions it once. Inverse document frequency down-weights terms that appear in many documents. A word like 'policy' appears in a large share of our corpus and is a weak signal, while 'sanctions' is rare and strongly informative.

TF-IDF multiplies the two. Its weakness is that term frequency grows without limit, so a very long document can dominate simply by repeating words. BM25 addresses this with saturation, controlled by the parameter k1, so each additional occurrence adds less to the score. It also normalises by document length, controlled by the parameter b, so that long documents are not unfairly favoured. Typical starting values are k1 between 1.2 and 2.0 and b around 0.75.

Before scoring, text must be tokenised consistently. Our pipeline will lower-case text, split on non-alphanumeric characters, remove common stop words and apply light stemming. An inverted index mapping each term to the documents containing it makes scoring efficient.""",
    },
    {
        "title": "Consumer Payment Preferences in Vietnam: Survey Findings",
        "category": "research",
        "doc_type": "Survey Report",
        "department": "Strategy & Insights",
        "tags": ["Market Research", "Payments", "Southeast Asia"],
        "summary": "Survey of 2,000 online shoppers on preferred payment methods, trust factors and reasons for abandoning checkout.",
        "content": """We surveyed two thousand online shoppers aged 18 to 55 across Hanoi, Ho Chi Minh City, Da Nang and Can Tho to understand how they prefer to pay and what causes them to abandon a purchase.

E-wallets were the most preferred payment method for orders under a moderate value, chosen by just over half of respondents. Bank transfer through QR codes was close behind and has grown rapidly since banks introduced instant interbank transfers. Cash on delivery remains popular for first purchases from an unfamiliar seller and for higher-value orders, where shoppers want to inspect goods before paying.

Card payments were the least preferred method overall, except among frequent online shoppers in the two largest cities. Respondents cited concerns about card data security and a lower rate of card ownership.

The most common reasons for abandoning checkout were unexpected shipping fees, a preferred payment method not being available and a slow or confusing payment process. Younger respondents were particularly sensitive to the number of steps required.

We recommend offering QR bank transfer as a first-class option on all checkout pages, showing shipping fees on the product page and keeping cash on delivery available for first-time customers while encouraging digital payment through small incentives.""",
    },
    {
        "title": "Sustainability Report: Scope 1 and 2 Emissions Baseline",
        "category": "research",
        "doc_type": "Report",
        "department": "Sustainability",
        "tags": ["Sustainability", "ESG", "Reporting"],
        "summary": "Establishes the company's first emissions baseline for offices, warehouses and the vehicle fleet, with methodology and reduction targets.",
        "content": """This report sets out Meridian Group's first measured baseline for direct and energy-related greenhouse gas emissions, following the Greenhouse Gas Protocol. The baseline year is 2025.

Scope 1 emissions are direct emissions from sources the company owns or controls. They come mainly from the diesel delivery vehicle fleet, with a smaller contribution from backup generators and refrigerants in warehouse cooling systems.

Scope 2 emissions come from purchased electricity used in offices, warehouses and the two data rooms. They were calculated using the location-based method with national grid emission factors and, separately, the market-based method reflecting renewable energy certificates purchased for the head office.

The vehicle fleet accounts for about 60 percent of combined Scope 1 and 2 emissions, warehouses for 30 percent and offices for the remainder. Data quality was highest for electricity, which is metered, and lowest for refrigerant leakage, which was estimated from service records.

The company commits to reducing combined Scope 1 and 2 emissions by 40 percent by 2030. The main levers are electrifying urban delivery vehicles as leases expire, installing rooftop solar at the two largest warehouses and replacing older cooling equipment with low-global-warming-potential refrigerants.""",
    },
    {
        "title": "Product Requirements: Document Repository Search v1",
        "category": "product",
        "doc_type": "Requirements",
        "department": "Product Management",
        "tags": ["Search", "Product Requirements", "Information Retrieval"],
        "summary": "Requirements for the first release of repository search: keyword search, filters, result snippets, logging and the success metrics we will track.",
        "content": """Problem: Employees struggle to find policies and procedures. In interviews, people described asking colleagues in chat instead of searching, because the old intranet search returned too many irrelevant results.

Goals for version one: allow users to find a known document within three attempts; support filtering by category, tag and date; show enough of each result to judge relevance without opening it; and capture the data needed to improve ranking in version two.

Functional requirements: a single search box available on every page; matching on title, summary and body text; filters for category, tag and date range that can be combined with a query; results showing title, summary, category, tags and publication date; pagination with ten results per page; and a clear message with suggestions when no results are found.

Logging requirements: every executed search records the query, the user if signed in, the filters applied and the number of results. Every click on a result records the query, the document and its position in the list. These logs must be exportable for offline analysis.

Success metrics: percentage of searches followed by a click on the first page, average position of the first click and share of searches with zero results. Version two will introduce ranked retrieval using BM25 and will be judged against the baseline collected in version one.""",
    },
    {
        "title": "User Research Synthesis: How Employees Find Policies",
        "category": "product",
        "doc_type": "Research Report",
        "department": "Product Management",
        "tags": ["User Research", "Search", "Customer Experience"],
        "summary": "Findings from 14 interviews and a diary study on how employees look for internal documents, where they get stuck and what they trust.",
        "content": """We interviewed fourteen employees from six departments and ran a two-week diary study with eight of them to understand how people find internal policies, procedures and research.

The first finding is that people search with task language, not document language. Participants typed queries such as 'how many days off can I carry over' rather than 'annual leave policy'. Search that only matches titles fails these users.

Second, trust depends on freshness and ownership. Participants were unsure whether a document was still valid when it had no visible owner or update date. Several described finding two conflicting versions of the same procedure.

Third, colleagues are the default search engine. When the first search failed, most participants asked a colleague in chat rather than refining their query. This creates a hidden cost for experienced staff, who answer the same questions repeatedly.

Fourth, filters are used when the result list is long, but only if they are visible without extra clicks. Category and date were the most valued filters.

Recommendations: search full text including summaries, display the owner and last updated date on every document, archive superseded versions clearly, and show filters alongside results on both desktop and mobile.""",
    },
    {
        "title": "Accessibility Standard for Web Interfaces (WCAG 2.2 AA)",
        "category": "product",
        "doc_type": "Standard",
        "department": "Design",
        "tags": ["Accessibility", "Design System", "Frontend"],
        "summary": "Minimum accessibility requirements for every web interface: colour contrast, keyboard navigation, focus states, alt text, forms and testing.",
        "content": """All new web interfaces, internal or external, must meet the Web Content Accessibility Guidelines version 2.2 at level AA. Accessibility is part of the definition of done, not a later phase.

Text must have a contrast ratio of at least 4.5 to 1 against its background, or 3 to 1 for large text. Interface components such as input borders and icons that convey meaning need a contrast of at least 3 to 1. Colour must never be the only way information is conveyed; error states, for example, also need an icon or text.

Every interactive element must be reachable and operable with a keyboard alone, in a logical order. Focus must always be visible and must not be hidden behind sticky headers. Custom components such as dropdowns and dialogs must follow established keyboard patterns.

Images that convey information need meaningful alternative text that describes their purpose, not their appearance. Decorative images use empty alternative text so screen readers skip them.

Form fields need visible labels, not just placeholder text. Error messages must identify the field and explain how to fix the problem. Touch targets should be at least 24 by 24 pixels.

Teams test with automated tools in the build pipeline and manually with a keyboard and a screen reader before each major release.""",
    },
    {
        "title": "Customer Feedback Loop: Closing the Loop on NPS Detractors",
        "category": "product",
        "doc_type": "Procedure",
        "department": "Customer Operations",
        "tags": ["Customer Experience", "NPS", "Customer Retention"],
        "summary": "Procedure for following up with customers who give a low Net Promoter Score, categorising feedback and feeding it into the product roadmap.",
        "content": """The Net Promoter Score survey is sent to customers 30 days after their first order and every six months thereafter. Customers who answer 0 to 6 are detractors, and research shows that a prompt, personal follow-up can recover a significant share of them.

Every detractor response with a comment is assigned to a customer success representative within one working day. The representative reads the customer's history, contacts them within three working days by their preferred channel and focuses on understanding the problem rather than defending the company.

Feedback is tagged using a fixed taxonomy: delivery, product quality, pricing, website usability, customer service and other. Consistent tagging allows trends to be tracked over time and compared between regions.

Where the issue can be fixed for the individual customer, such as a missing refund, the representative resolves it and records the outcome. Where the issue reflects a broader problem, it is logged in the product feedback board with a link to the customer conversation.

Each month, the customer experience team presents the top five detractor themes to product and operations leaders, together with the number of customers affected and any revenue at risk. Leaders commit to an owner and a response for each theme.""",
    },
    {
        "title": "Design System Guidelines: Buttons, Forms and Feedback",
        "category": "product",
        "doc_type": "Guide",
        "department": "Design",
        "tags": ["Design System", "Frontend", "Accessibility"],
        "summary": "Usage rules for primary and secondary buttons, form layout, validation timing and toast versus inline feedback in the company design system.",
        "content": """The design system provides shared components so that our products look and behave consistently. These guidelines explain when to use each component, not only how it looks.

Each view should have at most one primary button, representing the most likely next action. Secondary buttons are used for alternative actions and tertiary text buttons for low-emphasis actions such as cancel. Destructive actions use the danger style and always ask for confirmation when the result cannot be undone.

Button labels describe the outcome with a verb, such as 'Publish document' or 'Save changes'. Avoid generic labels such as 'OK' or 'Submit' when a more specific label is possible.

Forms use a single column with labels above fields. Group related fields with headings, and mark optional fields rather than required ones when most fields are required. Validate input when the user leaves a field or submits the form, not on every keystroke, so users are not interrupted while typing.

Use inline messages for feedback related to a specific field or section. Use toast notifications only for brief confirmations of completed actions that do not require a response. Errors that block progress must never be shown only in a toast, because toasts disappear and are easy to miss.""",
    },
    {
        "title": "Mobile App Release Process",
        "category": "product",
        "doc_type": "Procedure",
        "department": "Engineering",
        "tags": ["Mobile", "Deployment", "Process"],
        "summary": "Two-week release train for the iOS and Android apps, including feature flags, beta testing, staged rollout and hotfix criteria.",
        "content": """The mobile apps follow a two-week release train. A release branch is cut every second Tuesday, regardless of which features are ready. Features that are not complete are merged behind feature flags and remain switched off.

After the branch is cut, the build is distributed to internal testers and the external beta group. Quality assurance runs the regression suite on a matrix of supported devices and operating system versions. Only fixes for regressions are merged into the release branch.

The release is submitted to the app stores on the following Monday. Once approved, it is rolled out in stages: one percent of users on the first day, ten percent on the second, fifty percent on the fourth and full rollout after a week if crash-free sessions remain above the target.

If the crash rate rises or a serious bug is reported, the rollout is paused and the team decides whether to fix forward or roll back by remotely disabling the affected feature flag.

Hotfix releases outside the train are allowed only for crashes affecting more than a small share of users, security vulnerabilities, payment failures or legal requirements. Every hotfix is reviewed at the next retrospective.""",
    },
    {
        "title": "Customer Onboarding Email Sequence Playbook",
        "category": "product",
        "doc_type": "Playbook",
        "department": "Marketing",
        "tags": ["Customer Retention", "Email Marketing", "Customer Experience"],
        "summary": "Content, timing and success metrics for the six emails sent during a new customer's first 30 days, based on churn analysis findings.",
        "content": """The onboarding sequence is designed around the finding that customers who complete three core actions in their first two weeks are much more likely to stay. Every email therefore guides the customer towards one of those actions.

Email one is sent immediately after sign-up. It confirms the account, sets expectations about what the next few weeks will look like and links directly to the first core action. It contains a single call to action.

Email two arrives on day two and is triggered only if the first core action has not been completed. It shows a short example of a customer achieving a result in less than five minutes. Customers who have already completed the action receive a different message introducing the second action.

Emails three to five follow the same pattern, adapting to the customer's progress. Each email is short, uses plain language and avoids promotional offers, which reduced engagement in earlier tests.

Email six, sent on day 30, asks for feedback and invites customers to book a short call with the success team. Success is measured by the completion rate of core actions, not open rates, and every change to the sequence is tested against the current version with a holdout group.""",
    },
    {
        "title": "Service Level Agreement for Enterprise Customers",
        "category": "product",
        "doc_type": "Agreement",
        "department": "Customer Operations",
        "tags": ["SLA", "Customer Support", "Contracts"],
        "summary": "Availability commitments, support response times, maintenance windows and service credits offered to enterprise plan customers.",
        "content": """This service level agreement applies to customers on the enterprise plan and forms part of their subscription contract.

The platform is available at least 99.9 percent of the time in each calendar month, excluding scheduled maintenance. Availability is measured by external monitoring that checks the main application and the public API every minute from three locations.

Scheduled maintenance takes place in a weekly window outside business hours in the customer's primary region and is announced at least five days in advance. Emergency maintenance to address security vulnerabilities may be performed with shorter notice.

Support requests are answered according to severity. Critical issues, where the service is unavailable or data is at risk, receive a response within 30 minutes at any time. High-severity issues receive a response within two business hours, and normal issues within one business day. Enterprise customers have a named customer success manager.

If monthly availability falls below the commitment, the customer is entitled to a service credit calculated as a percentage of the monthly fee, increasing as availability falls further. Credits must be requested within 30 days of the end of the month and are the customer's sole financial remedy for availability shortfalls.""",
    },
    {
        "title": "Knowledge Base Writing Style Guide",
        "category": "product",
        "doc_type": "Guide",
        "department": "Customer Operations",
        "tags": ["Documentation", "Writing", "Customer Support"],
        "summary": "How to write help articles that customers can scan quickly: structure, titles, plain language, screenshots and keeping articles up to date.",
        "content": """Help articles exist to let customers solve problems without contacting support. A good article answers one question, can be scanned in seconds and stays accurate as the product changes.

Titles describe the task from the customer's point of view, starting with a verb where possible, such as 'Change your billing address' rather than 'Billing address settings'. Customers search for what they want to do, not for the name of a screen.

Begin with a one-sentence answer or summary, followed by numbered steps. Each step describes one action. Use the exact labels shown in the interface and format them in bold so customers can match them on screen.

Write in plain language at a level a busy reader can follow. Use short sentences, avoid internal jargon and spell out abbreviations on first use. Address the reader as 'you'.

Screenshots help when the location of a control is not obvious, but they become outdated quickly. Use them sparingly, crop them to the relevant area and add alternative text describing their content.

Every article has an owner and a review date. Articles that receive negative feedback from several readers, or that are linked from many support tickets, are reviewed first.""",
    },
]
