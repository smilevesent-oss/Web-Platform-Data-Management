# Seed documents, part 3: Finance & Procurement, Legal & Compliance.

DOCS = [
    {
        "title": "Procurement Policy and Purchasing Thresholds",
        "category": "finance",
        "doc_type": "Policy",
        "department": "Finance",
        "tags": ["Procurement", "Budget", "Approval Workflow"],
        "summary": "Sets the number of quotes required at each spend level, who may approve purchases and when a formal tender is mandatory.",
        "content": """The procurement policy ensures that the company obtains good value, treats suppliers fairly and can demonstrate how purchasing decisions were made.

Purchases below the low-value threshold may be made with a single quote and a company card, provided the supplier is not already under a framework agreement. Purchases between the low- and mid-value thresholds require at least three written quotes, and the reason for choosing the winning supplier must be recorded.

Above the mid-value threshold, a formal tender is mandatory. Procurement drafts the request for proposal with the business owner, publishes evaluation criteria in advance and convenes a panel of at least three people, including one from outside the requesting department, to score responses.

Approval authority depends on the total contract value over its full term, not the annual value. Splitting a purchase into smaller orders to stay below a threshold is prohibited and is checked by internal audit.

Employees involved in a purchase must declare any personal relationship with a bidding supplier. Gifts or hospitality offered by suppliers during a tender must be refused.""",
    },
    {
        "title": "Quarterly Financial Close Calendar and Responsibilities",
        "category": "finance",
        "doc_type": "Procedure",
        "department": "Finance",
        "tags": ["Financial Close", "Accounting", "Reporting"],
        "summary": "Day-by-day calendar for the quarterly close, from sub-ledger cut-off to consolidated reporting, with owners for each task.",
        "content": """The quarterly close is completed in eight working days. Day zero is the last calendar day of the quarter.

On working day one, sub-ledgers for accounts payable, accounts receivable and inventory are closed. Purchase orders received but not yet invoiced are accrued based on goods received notes. Payroll accruals are posted by the payroll team.

On day two, bank reconciliations are completed for all accounts, and intercompany balances are confirmed between entities. Differences above the materiality threshold are investigated the same day.

Days three and four are used for revenue recognition review, fixed asset depreciation, prepayment amortisation and foreign exchange revaluation. The revenue team reviews contracts with non-standard terms to confirm the timing of recognition.

On day five, local entity accounts are submitted for consolidation. Days six and seven cover consolidation adjustments, variance analysis against forecast and preparation of the management pack. On day eight, the Chief Financial Officer reviews and signs off the results.

Each task in the close checklist has a preparer and a reviewer, and evidence of review is stored with the working papers for the external auditors.""",
    },
    {
        "title": "Capital Expenditure Approval Process",
        "category": "finance",
        "doc_type": "Procedure",
        "department": "Finance",
        "tags": ["Budget", "Approval Workflow", "Investment"],
        "summary": "How to prepare a business case for capital investment, the required financial metrics and the approval levels for CapEx requests.",
        "content": """Capital expenditure covers purchases of assets that will benefit the company for more than one year, such as equipment, building improvements and capitalised software development.

Every request requires a business case describing the problem being solved, the options considered, the expected benefits and the risks. Requests above the departmental threshold must also include a net present value calculation using the company's hurdle rate, a payback period and a sensitivity analysis showing how the result changes if costs rise or benefits fall by 20 percent.

Business cases are reviewed first by the finance business partner, who checks assumptions and confirms the expenditure fits within the approved capital budget. Projects not included in the annual budget require a funding source to be identified.

Approval levels depend on total project cost. Department heads approve smaller projects, the Chief Financial Officer approves mid-sized projects and the investment committee approves major projects.

Approved projects report actual spending against budget monthly. A post-implementation review is completed twelve months after completion to compare realised benefits with those promised in the business case.""",
    },
    {
        "title": "Supplier Payment Terms and Invoice Processing",
        "category": "finance",
        "doc_type": "Procedure",
        "department": "Finance",
        "tags": ["Accounts Payable", "Invoices", "Procurement"],
        "summary": "Standard payment terms, three-way matching rules, how disputed invoices are handled and safeguards against bank detail fraud.",
        "content": """Standard payment terms are 30 days from receipt of a valid invoice. Small and medium suppliers that meet the eligibility criteria are paid within 15 days in line with the company's commitment to fair payment practices.

Invoices are processed through three-way matching: the invoice must match the purchase order and the goods received note within a small tolerance. Invoices that fail matching are held and routed to the requester for resolution.

Invoices without a valid purchase order number are returned to the supplier. Exceptions are limited to utilities, statutory fees and other categories listed in the accounts payable manual.

If an invoice is disputed, the requester must notify accounts payable within five working days, giving the reason. The undisputed portion is paid on normal terms.

Changes to supplier bank details are a common target for fraud. Any request to change bank details must be verified by a call to a contact number held on file, not one provided in the request, and approved by two members of the finance team. The supplier is notified by letter after the change is made.""",
    },
    {
        "title": "FY2027 Budget Planning Guidelines",
        "category": "finance",
        "doc_type": "Guide",
        "department": "Finance",
        "tags": ["Budget", "Planning", "Forecasting"],
        "summary": "Planning assumptions, the budgeting timeline and the templates departments must use when submitting their FY2027 operating budgets.",
        "content": """The FY2027 budget will be built bottom-up by departments and then reconciled with the top-down targets set by the executive committee. Submissions are due by the end of the second week of November.

Planning assumptions are provided centrally so that departments use consistent figures. These include salary increase pools, employer social security rates, inflation for general expenses and foreign exchange rates. Departments must not use their own assumptions for these items.

Headcount is planned by role and start month. New roles must be linked to a strategic initiative or a measurable increase in workload. Vacant roles that have been open for more than six months are removed unless the department head justifies keeping them.

Non-headcount spending is planned by category. Software subscriptions must be listed individually, with the number of licences, so that the procurement team can consolidate overlapping tools.

After submission, finance business partners hold review meetings with each department. Final budgets are approved by the board in December and loaded into the planning system, where actuals are tracked monthly.""",
    },
    {
        "title": "Corporate Card Usage Policy",
        "category": "finance",
        "doc_type": "Policy",
        "department": "Finance",
        "tags": ["Expenses", "Compliance", "Finance"],
        "summary": "Who receives a corporate card, permitted and prohibited purchases, monthly reconciliation and the consequences of misuse.",
        "content": """Corporate cards are issued to employees who regularly travel or make low-value purchases on behalf of the company. Cards are issued in the employee's name, and the employee is responsible for every transaction on the card.

Cards may be used for business travel, approved subscriptions, conference fees and small purchases below the low-value procurement threshold. They must not be used for personal expenses, cash withdrawals, gift cards or purchases from suppliers that should be paid by invoice under a contract.

Each month, cardholders must reconcile their transactions in the expense application within ten days of the statement date, attaching receipts and a business purpose for each item. Managers approve the reconciliation.

Accidental personal purchases must be reported immediately and repaid within the same month. Repeated personal use, late reconciliation or missing receipts may result in the card being suspended.

Lost or stolen cards must be reported to the card provider and to finance immediately. Cards are cancelled automatically when an employee leaves the company.""",
    },
    {
        "title": "Anti-Bribery and Corruption Policy",
        "category": "legal",
        "doc_type": "Policy",
        "department": "Legal",
        "tags": ["Compliance", "Code of Conduct", "Ethics"],
        "summary": "Prohibits bribes and facilitation payments, sets rules for gifts and hospitality, and explains due diligence on intermediaries and how to report concerns.",
        "content": """Meridian Group prohibits bribery in all its forms. Employees and anyone acting on the company's behalf must never offer, give, request or accept anything of value to improperly influence a business decision.

Facilitation payments, small unofficial payments to speed up routine government actions such as customs clearance, are prohibited even where they are customary locally. The only exception is when a payment is demanded under threat to personal safety; such payments must be reported to Legal immediately afterwards.

Gifts and hospitality may be offered or accepted only if they are modest, infrequent, given openly and not connected to a pending decision. All gifts and hospitality above the threshold value must be recorded in the gifts register. Anything involving public officials requires prior approval from Legal regardless of value.

Third parties who act on the company's behalf, such as agents, distributors and consultants, must undergo risk-based due diligence before engagement, and contracts must include anti-bribery clauses and audit rights.

Concerns can be raised with the compliance team or through the anonymous ethics hotline. The company will support any employee who refuses to pay a bribe, even if the refusal results in lost business.""",
    },
    {
        "title": "Personal Data Protection Policy",
        "category": "legal",
        "doc_type": "Policy",
        "department": "Legal",
        "tags": ["Data Protection", "Privacy", "Compliance"],
        "summary": "Explains the principles governing personal data, lawful bases for processing, data subject rights and the role of the Data Protection Officer.",
        "content": """Meridian Group processes personal data about customers, employees, suppliers and website visitors. This policy explains how that data must be handled to comply with data protection laws and to respect individuals' privacy.

Personal data must be processed lawfully, fairly and transparently; collected for specified purposes; limited to what is necessary; kept accurate; retained no longer than needed; and protected with appropriate security. These principles apply to every system and every team.

Each processing activity must have a lawful basis, such as performance of a contract, a legal obligation, legitimate interests or consent. Where consent is used, it must be freely given, specific and as easy to withdraw as to give.

Individuals have rights to access their data, correct it, request deletion, object to certain processing and receive a portable copy. Requests must be forwarded to the privacy team immediately, because the company generally has one month to respond.

New projects that involve high-risk processing, such as large-scale profiling or new monitoring technology, require a data protection impact assessment before launch. The Data Protection Officer advises on these assessments and is the contact point for regulators.""",
    },
    {
        "title": "Contract Review Checklist for Commercial Agreements",
        "category": "legal",
        "doc_type": "Checklist",
        "department": "Legal",
        "tags": ["Contracts", "Legal Review", "Vendor Management"],
        "summary": "Key clauses to check before signing a commercial agreement: liability caps, indemnities, termination, data protection and governing law.",
        "content": """Business teams may negotiate low-risk contracts using approved templates. Any deviation from the template, or any contract with a value above the delegated threshold, must be reviewed by Legal using this checklist.

Parties and scope: confirm the correct legal entities are named and that the description of services or goods matches what the business expects to receive. Vague scope is the most common cause of later disputes.

Liability: check that liability is capped at a reasonable multiple of the annual contract value, and that the cap does not apply to breaches of confidentiality, data protection or intellectual property where the company needs full protection.

Indemnities: the supplier should indemnify the company against third-party intellectual property claims arising from its products. Avoid accepting broad indemnities in favour of the supplier.

Term and termination: confirm the initial term, renewal mechanism and notice periods. The company should be able to terminate for convenience with reasonable notice and immediately for material breach or insolvency.

Data protection and security: where the supplier processes personal data, the data processing addendum must be attached and the security assessment must be approved. Finally, confirm governing law and the dispute resolution forum.""",
    },
    {
        "title": "Whistleblowing Policy and Speak-Up Channels",
        "category": "legal",
        "doc_type": "Policy",
        "department": "Legal",
        "tags": ["Ethics", "Compliance", "Code of Conduct"],
        "summary": "Who can raise concerns, what can be reported, the confidential and anonymous channels available and how whistleblowers are protected.",
        "content": """Meridian Group wants employees and partners to speak up when they suspect wrongdoing. Early reporting allows problems to be fixed before they cause serious harm.

The policy covers concerns about fraud, bribery, financial misreporting, breaches of law or regulation, health and safety dangers, environmental damage and attempts to conceal any of these. Personal grievances about employment terms are handled under the grievance procedure instead.

Concerns can be raised with a line manager, the compliance team, the General Counsel or the independent hotline, which is operated by an external provider and allows anonymous reports. Anonymous reporters receive a reference number to check progress and answer follow-up questions.

Reports are assessed by the compliance team within seven days. Investigations are carried out by people independent of the matter, and the reporter is informed when the investigation is complete, though details may be limited by confidentiality.

Anyone who raises a concern in good faith is protected from retaliation, even if the concern turns out to be unfounded. Retaliation is a disciplinary offence. Deliberately false reports made maliciously may also lead to disciplinary action.""",
    },
    {
        "title": "Export Control and Sanctions Screening Procedure",
        "category": "legal",
        "doc_type": "Procedure",
        "department": "Legal",
        "tags": ["Sanctions", "Compliance", "Trade"],
        "summary": "How customers, suppliers and shipments are screened against sanctions lists, how products are classified and what to do with a potential match.",
        "content": """International sanctions and export controls restrict trade with certain countries, organisations and individuals, and limit the export of some technologies. Breaches can result in heavy fines and criminal liability.

All new customers, suppliers and distributors are screened against consolidated sanctions lists before onboarding. Existing counterparties are rescreened automatically whenever the lists are updated.

A potential match is placed on hold and reviewed by the compliance team. Most potential matches are false positives caused by common names; the reviewer compares additional identifiers such as address, date of birth or registration number before clearing or escalating the match.

Products and software are classified under the applicable export control lists. Items that include strong encryption may require a licence or a notification before export to certain destinations. The product team maintains the classification of each product and updates it when features change.

Shipments to high-risk destinations require an end-use declaration from the customer. Employees must stop a transaction and contact Legal if they notice red flags, such as a customer reluctant to explain the end use or requesting unusual shipping routes.""",
    },
    {
        "title": "Intellectual Property and Open Source Usage Policy",
        "category": "legal",
        "doc_type": "Policy",
        "department": "Legal",
        "tags": ["Intellectual Property", "Open Source", "Licensing"],
        "summary": "Ownership of work created by employees, rules for using open source licences in products and the process for contributing to external projects.",
        "content": """Inventions, code, documents and designs created by employees in the course of their work belong to the company. Employees must not use company resources to develop personal projects that compete with company products.

Open source software is widely used in company products and is encouraged, provided licence obligations are respected. Licences are grouped into three categories. Permissive licences such as MIT, BSD and Apache 2.0 may be used freely with attribution. Weak copyleft licences such as LGPL and MPL may be used with care, usually as unmodified separate components. Strong copyleft licences such as GPL and AGPL require Legal approval before use in any distributed or network-accessible product.

All dependencies are scanned automatically in the build pipeline, and a software bill of materials is generated for every release. New licences that are not on the approved list block the build until reviewed.

Employees may contribute to external open source projects related to their work after registering the project with the open source programme office. Contributions must not include confidential information, and contributor licence agreements are signed by Legal on the company's behalf.""",
    },
    {
        "title": "Competition Law Compliance Guidelines",
        "category": "legal",
        "doc_type": "Guide",
        "department": "Legal",
        "tags": ["Competition Law", "Compliance", "Ethics"],
        "summary": "Practical dos and don'ts for interactions with competitors, trade associations and distributors to avoid anti-competitive agreements.",
        "content": """Competition law prohibits agreements and practices that restrict fair competition. Penalties can reach a significant percentage of global turnover, and individuals can face personal liability.

Never discuss with competitors prices, discounts, margins, capacity, bidding intentions, customer allocation or future commercial strategy. This applies to formal meetings, informal conversations at conferences and messaging apps. An understanding does not need to be written down to be illegal.

Trade association meetings are permitted but must have a written agenda reviewed in advance, minutes must be kept, and a lawyer should attend when sensitive topics are discussed. If a conversation moves to prohibited subjects, object clearly, leave the meeting and ask for your departure to be minuted, then inform Legal.

Distributors and resellers must remain free to set their own resale prices. The company may suggest a recommended retail price but must not pressure distributors to follow it.

Where the company has a strong market position, additional rules apply, such as restrictions on exclusivity arrangements and below-cost pricing. Consult Legal before introducing new discount schemes or exclusive deals.""",
    },
    {
        "title": "Data Protection Impact Assessment Template and Guidance",
        "category": "legal",
        "doc_type": "Template",
        "department": "Legal",
        "tags": ["Data Protection", "Privacy", "Risk Management"],
        "summary": "When a DPIA is required, how to describe the processing, assess necessity and risks to individuals, and record mitigation measures.",
        "content": """A data protection impact assessment is required before starting any processing that is likely to result in a high risk to individuals. Examples include large-scale processing of sensitive data, systematic monitoring of employees, automated decisions with significant effects and combining datasets from different sources.

Section one describes the processing: what personal data will be collected, from whom, for what purpose, where it will be stored, who will have access and how long it will be retained. A data flow diagram is strongly recommended.

Section two assesses necessity and proportionality. Explain why each data item is needed, whether the purpose could be achieved with less data, and which lawful basis applies.

Section three identifies risks to individuals, such as discrimination, loss of confidentiality, identity theft or loss of control over their data. Each risk is rated by likelihood and severity.

Section four records measures to reduce each risk, such as pseudonymisation, access restrictions, shorter retention or giving individuals an easy way to opt out. The residual risk after mitigation is rated again.

The completed assessment is reviewed by the Data Protection Officer. If high residual risk remains, the regulator must be consulted before processing begins.""",
    },
]
