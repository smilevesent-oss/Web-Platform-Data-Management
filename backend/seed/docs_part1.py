# Seed documents, part 1: Human Resources and Information Security.
# Each entry: title, category key, doc_type, department, tags, summary, content.
# The organisation ("Meridian Group") is fictional; the practices described are realistic.

DOCS = [
    {
        "title": "Remote and Hybrid Work Policy 2026",
        "category": "hr",
        "doc_type": "Policy",
        "department": "People & Culture",
        "tags": ["Remote Work", "Hybrid", "Employee Handbook"],
        "summary": "Defines who is eligible for hybrid or fully remote work, core collaboration hours, equipment allowances and how managers approve work-location changes.",
        "content": """Meridian Group operates a hybrid-first model. Most roles are expected on site two days per week, chosen by each team so that people who collaborate closely overlap. Fully remote arrangements are approved case by case for roles that do not depend on physical equipment or in-person client work.

Core collaboration hours are 10:00 to 15:00 in the employee's home time zone. Meetings that involve more than one team should be scheduled inside this window. Outside it, employees may arrange their day flexibly as long as deadlines and service levels are met.

Employees working remotely receive a one-time home office allowance for a chair, monitor and headset, plus a monthly connectivity stipend. Company laptops must be used for all work; personal devices may only access e-mail and chat through the managed mobile application.

A request to change work location is submitted through the HR portal and approved by the line manager and the HR business partner. Approvals are reviewed every twelve months or when the role changes. Working from another country for more than 14 days requires prior approval from Legal because of tax and immigration implications.

Managers are expected to evaluate performance on outcomes rather than visibility. Teams should document decisions in shared channels so that colleagues who were not in the room have the same information as those who were.""",
    },
    {
        "title": "Annual Leave and Public Holiday Guidelines",
        "category": "hr",
        "doc_type": "Policy",
        "department": "People & Culture",
        "tags": ["Leave", "Employee Handbook", "Payroll"],
        "summary": "Explains annual leave entitlement, accrual, carry-over limits, blackout periods and the procedure for booking public holidays and compensatory days.",
        "content": """Full-time employees accrue 18 days of paid annual leave per calendar year, rising by one day for every three full years of service up to a maximum of 24 days. Part-time employees accrue leave pro rata to their contracted hours.

Leave accrues monthly and can be taken as soon as it has been earned. Up to five unused days may be carried into the first quarter of the following year; any balance beyond that expires on 31 March unless a business-critical project prevented it from being taken and the department head has approved an extension in writing.

Requests should be made through the HR portal at least two weeks in advance for absences longer than three days. Finance and customer support teams observe a blackout period during the last five working days of each quarter, when leave is granted only in exceptional circumstances.

Employees who are asked to work on a public holiday receive a compensatory day off, to be taken within 60 days, in addition to any statutory overtime premium. Compensatory days cannot be converted to cash.

When an employee leaves the company, accrued but unused leave is paid out in the final salary in line with local labour law.""",
    },
    {
        "title": "Performance Review Cycle: Manager Handbook",
        "category": "hr",
        "doc_type": "Guide",
        "department": "People & Culture",
        "tags": ["Performance", "Management", "Career Development"],
        "summary": "Step-by-step guide for managers running the semi-annual review: goal setting, evidence collection, calibration meetings and delivering ratings.",
        "content": """The performance cycle runs twice a year, with a mid-year check-in in June and a full review in December. Each cycle has four stages: self-assessment, manager assessment, calibration and the feedback conversation.

Goals should be set at the start of each half using the outcome-measure-deadline format. A good goal states what will change, how progress will be observed and when it is due. Managers should agree no more than five goals with each report, and at least one should relate to growing a skill.

When writing the assessment, collect evidence throughout the period instead of relying on memory. Peer feedback, delivered work and customer outcomes are stronger evidence than general impressions. Avoid comparing an employee to colleagues in the written review; comparisons belong in calibration.

Calibration meetings bring together managers in the same function to align on standards. Each manager presents proposed ratings with two or three concrete examples. HR facilitates and checks for patterns such as consistently lower ratings for part-time staff or recent parents.

The feedback conversation should happen within two weeks of calibration. Share the rating early in the meeting, explain the evidence, and spend most of the time on development for the next half.""",
    },
    {
        "title": "Employee Onboarding Checklist for New Hires",
        "category": "hr",
        "doc_type": "Checklist",
        "department": "People & Culture",
        "tags": ["Onboarding", "Employee Handbook", "IT Access"],
        "summary": "A practical first-30-days checklist covering paperwork, IT accounts, mandatory training, buddy assignment and the 30-day check-in with the manager.",
        "content": """Before day one, HR sends the employment contract, tax forms and the equipment delivery schedule. The hiring manager nominates an onboarding buddy from the same team and blocks thirty minutes with them in the first week.

On day one, the new hire collects their laptop and access badge, signs the acceptable use policy and activates multi-factor authentication. IT support runs a short session on the password manager, VPN and the internal service desk.

During the first week, the employee completes the mandatory training modules: information security awareness, data protection basics, anti-bribery and the code of conduct. Each takes less than 40 minutes. Completion is tracked automatically and reminders are sent after five working days.

By the end of week two the manager should have shared the team's current priorities, introduced key stakeholders and agreed three onboarding goals. These goals are deliberately small, for example shipping a first change, shadowing a customer call or reviewing a process document.

At day 30 the manager holds a structured check-in covering what is going well, what is confusing and what support is missing. Feedback from these check-ins is reviewed quarterly by People & Culture to improve the programme.""",
    },
    {
        "title": "Learning and Development Budget Policy",
        "category": "hr",
        "doc_type": "Policy",
        "department": "People & Culture",
        "tags": ["Career Development", "Training", "Budget"],
        "summary": "Each employee has an annual learning budget for courses, certifications and conferences; this policy covers eligibility, approval and repayment rules.",
        "content": """Every permanent employee who has passed probation receives an individual learning budget each year. The budget can be spent on courses, professional certifications, books, conference tickets and associated travel when the event is relevant to the employee's current or planned role.

Requests under the threshold set by Finance need only line-manager approval. Larger requests, or anything involving international travel, also require approval from the department head. Requests should explain the expected benefit to the role in two or three sentences.

Certifications that take more than 40 study hours qualify for up to three days of paid study leave. Exam fees are covered for the first attempt; a second attempt is covered if the manager agrees the first was taken in good faith.

If an employee resigns within twelve months of completing a certification that cost more than half of their annual budget, a pro-rated share must be repaid. This clause does not apply to redundancy or to resignations approved on medical grounds.

Unused budget does not roll over. Teams are encouraged to share what they learned through short internal talks or written summaries in this repository.""",
    },
    {
        "title": "Workplace Harassment Prevention and Reporting Procedure",
        "category": "hr",
        "doc_type": "Procedure",
        "department": "People & Culture",
        "tags": ["Code of Conduct", "Compliance", "Employee Wellbeing"],
        "summary": "Sets out what counts as harassment, the confidential reporting channels available, investigation timelines and protection against retaliation.",
        "content": """Meridian Group does not tolerate harassment, bullying or discrimination of any kind, whether in the office, at client sites, at company events or in online channels. This includes unwelcome comments, jokes or messages relating to gender, ethnicity, religion, age, disability, sexual orientation or any other protected characteristic.

Employees can raise a concern with their manager, their HR business partner or through the independent ethics hotline, which accepts anonymous reports by phone or web form twenty-four hours a day. Reports involving a senior leader are routed directly to the Chief People Officer and the General Counsel.

Every report is acknowledged within two working days. An investigator who has no reporting relationship with either party is assigned within five working days. Investigations normally conclude within thirty days, and both parties are informed of the outcome to the extent allowed by privacy law.

Interim measures, such as changing reporting lines or working locations, may be put in place during the investigation to protect the people involved. These measures are not a judgement on the outcome.

Retaliation against anyone who raises a concern in good faith, or who takes part in an investigation, is itself a serious disciplinary offence.""",
    },
    {
        "title": "Parental Leave and Return-to-Work Programme",
        "category": "hr",
        "doc_type": "Policy",
        "department": "People & Culture",
        "tags": ["Leave", "Employee Wellbeing", "Benefits"],
        "summary": "Describes paid parental leave for all parents, keeping-in-touch days and the phased return schedule that helps parents transition back to work.",
        "content": """All employees who become parents through birth, adoption or surrogacy are entitled to paid parental leave. Primary caregivers receive 20 weeks at full pay, and secondary caregivers receive eight weeks at full pay, which may be taken in up to three blocks within the first year.

Employees should inform HR at least eight weeks before the expected start date. HR will confirm entitlements, explain statutory benefits that run alongside the company scheme and arrange a handover plan with the manager.

During leave, employees may take up to ten optional keeping-in-touch days. These are paid in addition to leave pay and can be used for training, team events or planning the return. Managers must not contact employees on leave about routine work.

The return-to-work programme offers a phased schedule: 60 percent of contracted hours in the first two weeks and 80 percent in weeks three and four, at full pay. Parents may also request a flexible working pattern, which will be considered in good faith.

Performance ratings for a cycle that includes parental leave are based only on the period worked and must not be reduced because of the absence.""",
    },
    {
        "title": "Information Security Policy",
        "category": "security",
        "doc_type": "Policy",
        "department": "Information Security",
        "tags": ["Security", "ISO 27001", "Compliance"],
        "summary": "The top-level security policy: governance, risk ownership, data classification, access control principles and the responsibilities of every employee.",
        "content": """This policy sets the direction for protecting the confidentiality, integrity and availability of Meridian Group information. It applies to all employees, contractors and third parties who access company systems or data.

The Chief Information Security Officer owns the security programme and reports quarterly to the Executive Risk Committee. Each business system has a named owner who is accountable for its risk assessment, access reviews and incident response plan.

Information is classified into four levels: Public, Internal, Confidential and Restricted. The classification determines how data may be stored, shared and destroyed. Restricted data, which includes customer personal data and unreleased financial results, must be encrypted at rest and in transit and may only be shared with named individuals.

Access is granted on the principle of least privilege and is reviewed every six months. Shared accounts are prohibited except for documented service accounts with an owner. Multi-factor authentication is mandatory for all remote access and all administrative interfaces.

Every employee is responsible for completing annual security training, reporting suspected incidents immediately and locking their device when unattended. Breaches of this policy may lead to disciplinary action.""",
    },
    {
        "title": "Password and Multi-Factor Authentication Standard",
        "category": "security",
        "doc_type": "Standard",
        "department": "Information Security",
        "tags": ["Security", "Authentication", "IT Access"],
        "summary": "Technical standard for password length, password manager use, MFA methods ranked by strength and requirements for service accounts.",
        "content": """Passwords protect access to company systems only when they are long, unique and never reused. This standard follows current NIST guidance and replaces the older rule of forced 90-day rotation.

User passwords must be at least 14 characters. Passphrases made of several unrelated words are encouraged. Passwords are checked against a list of known breached passwords at the time they are set. Rotation is required only when there is evidence or suspicion of compromise.

All employees must store work credentials in the company password manager. Writing passwords in documents, chat messages or browser storage on unmanaged devices is not permitted.

Multi-factor authentication is mandatory. Approved methods, from strongest to weakest, are hardware security keys, platform passkeys, authenticator app push with number matching and time-based one-time codes. SMS codes are allowed only as a temporary recovery method. Administrators must use a hardware key or passkey.

Service accounts must use secrets of at least 32 random characters stored in the secrets vault, with automated rotation at least every 180 days. Secrets must never be committed to source control; repositories are scanned automatically and any detected secret is revoked.""",
    },
    {
        "title": "Security Incident Response Playbook",
        "category": "security",
        "doc_type": "Playbook",
        "department": "Information Security",
        "tags": ["Incident Response", "Security", "On-Call"],
        "summary": "Severity definitions, roles and the six phases of incident handling, from detection and containment to post-incident review.",
        "content": """A security incident is any event that threatens the confidentiality, integrity or availability of company information. Suspected incidents must be reported immediately through the security hotline or the incident channel; it is always better to report something that turns out to be harmless.

Incidents are classified into four severities. SEV1 covers confirmed breaches of restricted data or a complete outage of a critical service. SEV2 covers active compromise that is contained to a limited scope. SEV3 covers suspicious activity requiring investigation, and SEV4 covers policy violations without immediate risk.

Every incident above SEV3 has an Incident Commander who coordinates the response, a Technical Lead who directs investigation, and a Communications Lead who handles updates to leadership, customers and regulators. The Incident Commander does not do hands-on technical work.

Response follows six phases: identification, containment, eradication, recovery, notification and lessons learned. Evidence such as logs and disk images must be preserved before systems are rebuilt.

When personal data is affected, the Data Protection Officer must be informed within four hours so that regulatory notification deadlines can be met. A blameless post-incident review is held within ten working days and its actions are tracked to completion.""",
    },
    {
        "title": "Phishing Awareness: How to Spot a Malicious Email",
        "category": "security",
        "doc_type": "Guide",
        "department": "Information Security",
        "tags": ["Security", "Training", "Phishing"],
        "summary": "Practical signs of phishing, examples from recent simulated campaigns and what to do if you clicked a suspicious link.",
        "content": """Phishing remains the most common way attackers gain a foothold in organisations. Most phishing messages rely on urgency, authority or curiosity to make the recipient act before thinking.

Common warning signs include a sender address that does not match the display name, unexpected attachments, requests to bypass normal approval processes and links whose real destination differs from the text shown. Hover over a link before clicking to see where it really goes.

In last quarter's simulation, the most clicked message impersonated a shared-document notification with a deadline of the same day. The second most effective pretended to be a parcel delivery that required a small customs payment. Both relied on everyday tasks that people perform without much attention.

Payment change requests deserve special care. If a supplier or executive asks by e-mail to change bank details or to make an urgent transfer, verify the request by calling a phone number you already have, never one supplied in the message.

If you clicked a link or entered credentials, do not feel embarrassed. Report it to the security team immediately using the Report Phishing button and change your password. Fast reporting is what turns a potential breach into a non-event.""",
    },
    {
        "title": "Data Classification and Handling Standard",
        "category": "security",
        "doc_type": "Standard",
        "department": "Information Security",
        "tags": ["Data Protection", "Security", "Compliance"],
        "summary": "Defines Public, Internal, Confidential and Restricted data, with concrete handling rules for storage, sharing, printing and disposal.",
        "content": """Every document, dataset and system must be assigned one of four classification levels. When in doubt, choose the higher level and ask the data owner.

Public information has been approved for release, such as marketing material and published reports. It may be shared freely.

Internal information is intended for employees and approved contractors, such as organisation charts and internal announcements. It may be stored in any company-managed system but must not be posted on public websites.

Confidential information could harm the company or its partners if disclosed, such as contracts, pricing models and source code. It must be stored only in approved systems with access restricted to the teams that need it, and shared externally only under a non-disclosure agreement.

Restricted information includes customer personal data, payment data, health information and unreleased financial results. It must be encrypted at rest and in transit, access must be logged, and it must never be copied to removable media or personal cloud storage. Printing is discouraged and printed copies must be shredded.

Data retention periods are listed in the Records Retention Schedule. When data reaches the end of its retention period it must be deleted securely, including from backups at their next rotation.""",
    },
    {
        "title": "Vulnerability Management and Patching SLA",
        "category": "security",
        "doc_type": "Standard",
        "department": "Information Security",
        "tags": ["Security", "Patching", "Infrastructure"],
        "summary": "Required remediation times for vulnerabilities by severity, the scanning cadence and the exception process when a patch cannot be applied in time.",
        "content": """All servers, containers, endpoints and network devices are scanned for vulnerabilities at least weekly. Internet-facing systems and container images are additionally scanned on every build.

Findings are prioritised using the CVSS base score adjusted for exploitability and exposure. A medium-severity issue on an internet-facing system that is being actively exploited may be treated as critical.

Remediation deadlines are as follows. Critical vulnerabilities must be fixed or mitigated within 72 hours. High vulnerabilities must be fixed within 14 days, medium within 45 days and low within 90 days. The clock starts when the finding is first reported to the system owner.

When a patch cannot be applied in time, for example because a vendor has not released a fix or a change freeze is in effect, the system owner must file an exception describing compensating controls such as network isolation or a web application firewall rule. Exceptions are approved by the security team and expire after 90 days.

Compliance with these deadlines is reported monthly to engineering leadership. Teams with recurring overdue findings are asked to present a remediation plan at the architecture review board.""",
    },
    {
        "title": "Acceptable Use of Generative AI Tools",
        "category": "security",
        "doc_type": "Policy",
        "department": "Information Security",
        "tags": ["Artificial Intelligence", "Data Protection", "Security"],
        "summary": "Rules for using AI assistants at work: approved tools, what data may be entered, review of generated output and disclosure requirements.",
        "content": """Generative AI tools can speed up drafting, coding and analysis, but they also create risks of data leakage, inaccurate output and intellectual property issues. This policy explains how employees may use them safely.

Only tools on the approved list may be used with company data. Approved enterprise tools have contractual commitments that inputs are not used to train public models and that data is retained only for a limited period. Consumer versions of the same tools are not approved.

Public and Internal information may be entered into approved tools. Confidential information may be entered only into tools approved for that level. Restricted data, including customer personal data and unreleased financial information, must never be entered into any AI tool.

Employees remain responsible for anything they publish or ship, regardless of how it was produced. Generated code must pass the same review and testing as human-written code, and factual claims in generated text must be checked against reliable sources.

Content that is published externally and was substantially generated by AI should be disclosed according to the communications team's guidance. Questions about new tools or use cases should be raised with the security team before adoption.""",
    },
    {
        "title": "Third-Party Vendor Security Assessment Procedure",
        "category": "security",
        "doc_type": "Procedure",
        "department": "Information Security",
        "tags": ["Vendor Management", "Security", "Procurement"],
        "summary": "How vendors are tiered by risk, which questionnaires and certifications are required, and how assessments feed into contract approval.",
        "content": """Any supplier that will store, process or access Meridian Group data must pass a security assessment before a contract is signed. The procurement team triggers the assessment when a purchase request is raised.

Vendors are placed into three tiers. Tier 1 vendors handle Restricted data or provide critical services; Tier 2 vendors handle Confidential data; Tier 3 vendors handle only Public or Internal data.

Tier 1 vendors must provide an independent audit report such as SOC 2 Type II or ISO 27001 certification, complete the full security questionnaire and agree to the data processing addendum. The security team may also request a penetration test summary. Tier 2 vendors complete the standard questionnaire. Tier 3 vendors complete a short self-declaration.

The security team reviews responses within ten working days and issues one of three outcomes: approved, approved with conditions or not approved. Conditions, such as enabling single sign-on or restricting data residency, are written into the contract.

Tier 1 vendors are reassessed annually and Tier 2 vendors every two years. A vendor that suffers a breach affecting company data is immediately reassessed regardless of schedule.""",
    },
]
