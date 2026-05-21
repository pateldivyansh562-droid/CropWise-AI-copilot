"""
schemes/schemes_data.py
────────────────────────────────────────────────────────
All Government of India agricultural schemes.
Each scheme has:
  - id, name, name_hi (Hindi name)
  - tagline, tagline_hi
  - category, color, icon
  - description / description_hi
  - benefits list / benefits_hi
  - eligibility / eligibility_hi
  - how_to_apply / how_to_apply_hi
  - documents required
  - official_link
  - ai_context  — rich paragraph fed to the AI so it can answer any question
"""

SCHEMES: list[dict] = [
    {
        "id": "pm-kisan",
        "name": "PM-KISAN",
        "name_hi": "पीएम-किसान",
        "tagline": "₹6,000/year direct income support",
        "tagline_hi": "₹6,000 प्रति वर्ष सीधी आय सहायता",
        "category": "Income Support",
        "category_hi": "आय सहायता",
        "icon": "💰",
        "color": "#15803d",
        "description": (
            "Pradhan Mantri Kisan Samman Nidhi (PM-KISAN) provides income support of ₹6,000 per year "
            "to all landholding farmer families across India. The amount is paid in three equal instalments "
            "of ₹2,000 directly into the farmer's bank account via Direct Benefit Transfer (DBT). "
            "Launched in February 2019, it covers over 11 crore farmers."
        ),
        "description_hi": (
            "प्रधानमंत्री किसान सम्मान निधि (PM-KISAN) देश के सभी भूमि-धारक किसान परिवारों को "
            "₹6,000 प्रति वर्ष की आय सहायता प्रदान करती है। यह राशि ₹2,000 की तीन समान किस्तों में "
            "सीधे बैंक खाते में DBT के माध्यम से दी जाती है।"
        ),
        "benefits": [
            "₹6,000 per year in 3 instalments of ₹2,000 each",
            "Direct transfer to bank account — no middlemen",
            "Covers all landholding farmer families",
            "No upper income limit (except for exclusion categories)",
        ],
        "benefits_hi": [
            "₹6,000 प्रति वर्ष — ₹2,000 की 3 किस्तों में",
            "सीधे बैंक खाते में — कोई बिचौलिया नहीं",
            "सभी भूमिधारक किसान परिवारों को लाभ",
            "कोई आय सीमा नहीं (कुछ अपवादों को छोड़कर)",
        ],
        "eligibility": [
            "Must be a landholding farmer family",
            "Land records must be in the farmer's name",
            "Aadhaar linked bank account required",
            "Excludes: institutional landholders, former/current govt employees, taxpayers, professionals",
        ],
        "eligibility_hi": [
            "भूमिधारक किसान परिवार होना जरूरी है",
            "भूमि रिकॉर्ड किसान के नाम होना चाहिए",
            "आधार से जुड़ा बैंक खाता जरूरी है",
            "संस्थागत भूमिधारक, सरकारी कर्मचारी, आयकर दाता पात्र नहीं",
        ],
        "how_to_apply": [
            "Visit pmkisan.gov.in or nearest Common Service Centre (CSC)",
            "Register with Aadhaar number, bank account, and land records",
            "Village Patwari/Revenue Officer can verify and submit",
            "Check status at pmkisan.gov.in > Beneficiary Status",
        ],
        "how_to_apply_hi": [
            "pmkisan.gov.in पर जाएं या नजदीकी CSC केंद्र पर जाएं",
            "आधार नंबर, बैंक खाता और जमीन के कागज लेकर पंजीकरण करें",
            "पटवारी/राजस्व अधिकारी से सत्यापन कराएं",
            "pmkisan.gov.in > लाभार्थी स्थिति पर जांचें",
        ],
        "documents": ["Aadhaar Card", "Bank Passbook", "Land Records (Khasra/Khatauni)", "Mobile Number"],
        "official_link": "https://pmkisan.gov.in",
        "ai_context": (
            "PM-KISAN (Pradhan Mantri Kisan Samman Nidhi) is a Central Sector Scheme launched on 24 February 2019. "
            "It provides ₹6,000 per year income support to all farmer families holding cultivable land, "
            "paid as three instalments of ₹2,000 each (typically April-July, August-November, December-March). "
            "Registration can be done at pmkisan.gov.in, CSC centres, or through the Patwari. "
            "After registration, e-KYC with Aadhaar is mandatory. Instalment status can be checked on the portal. "
            "Excluded categories: institutional landholders, former/current MPs/MLAs/Ministers, Class 1/2 govt employees, "
            "income tax payers, doctors/engineers/lawyers/CAs/architects. "
            "If instalment is stuck, the farmer should check: Aadhaar-bank seeding, e-KYC completion, correct bank IFSC, "
            "land records updated. Helpline: 155261 / 011-24300606."
        ),
    },
    {
        "id": "pmfby",
        "name": "PMFBY",
        "name_hi": "पीएमएफबीवाई",
        "tagline": "Crop insurance at minimal premium",
        "tagline_hi": "न्यूनतम प्रीमियम पर फसल बीमा",
        "category": "Crop Insurance",
        "category_hi": "फसल बीमा",
        "icon": "🛡️",
        "color": "#1d4ed8",
        "description": (
            "Pradhan Mantri Fasal Bima Yojana (PMFBY) provides financial support to farmers suffering crop loss "
            "due to natural calamities, pests, and diseases. Farmers pay very low premiums (2% for Kharif, "
            "1.5% for Rabi, 5% for horticulture) while the rest is borne by the government."
        ),
        "description_hi": (
            "पीएमएफबीवाई प्राकृतिक आपदाओं, कीट और बीमारियों से फसल नुकसान पर वित्तीय सहायता देती है। "
            "किसान बहुत कम प्रीमियम देते हैं (खरीफ 2%, रबी 1.5%, बागवानी 5%) और बाकी सरकार देती है।"
        ),
        "benefits": [
            "Covers losses from drought, flood, hailstorm, cyclone, pest and disease",
            "Premium: only 2% for Kharif, 1.5% for Rabi crops",
            "Full sum insured paid if crop loss exceeds threshold",
            "Covers post-harvest losses for 14 days",
            "On-account payment for mid-season calamities",
        ],
        "benefits_hi": [
            "सूखा, बाढ़, ओलावृष्टि, चक्रवात, कीट-रोग से नुकसान कवर",
            "प्रीमियम: खरीफ 2%, रबी 1.5% मात्र",
            "थ्रेशहोल्ड से अधिक नुकसान पर पूरी बीमित राशि",
            "14 दिन तक कटाई के बाद का नुकसान भी कवर",
            "मौसम के बीच आपदा पर अग्रिम भुगतान",
        ],
        "eligibility": [
            "All farmers growing notified crops in notified areas",
            "Loanee farmers enrolled compulsorily under KCC loans",
            "Non-loanee farmers can enroll voluntarily",
            "Tenant/sharecropper farmers are also eligible",
        ],
        "eligibility_hi": [
            "अधिसूचित क्षेत्रों में अधिसूचित फसल उगाने वाले किसान",
            "KCC ऋणी किसानों के लिए अनिवार्य",
            "गैर-ऋणी किसान स्वैच्छिक रूप से शामिल हो सकते हैं",
            "बटाईदार और काश्तकार किसान भी पात्र हैं",
        ],
        "how_to_apply": [
            "Apply at nearest bank branch, CSC, or pmfby.gov.in",
            "Loanee farmers: bank enrolls automatically at crop loan disbursement",
            "Non-loanee: apply before cut-off date (usually 31 July for Kharif)",
            "For claims: report crop loss within 72 hours via Crop Insurance App or helpline 14447",
        ],
        "how_to_apply_hi": [
            "नजदीकी बैंक, CSC या pmfby.gov.in पर आवेदन करें",
            "ऋणी किसान: बैंक फसल ऋण के समय स्वतः नामांकन करता है",
            "गैर-ऋणी: अंतिम तिथि से पहले आवेदन करें (खरीफ के लिए 31 जुलाई)",
            "दावे के लिए: 72 घंटे के अंदर फसल बीमा ऐप या 14447 पर सूचित करें",
        ],
        "documents": ["Aadhaar Card", "Bank Passbook", "Land Records", "Sowing Certificate", "KCC (if applicable)"],
        "official_link": "https://pmfby.gov.in",
        "ai_context": (
            "PMFBY (Pradhan Mantri Fasal Bima Yojana) launched in 2016 replaced earlier NAIS/MNAIS schemes. "
            "Premium rates are capped at 2% for Kharif, 1.5% for Rabi, 5% for annual horticulture — rest paid by state+centre. "
            "Coverage: prevented sowing, mid-season adversity, post-harvest (14 days), localised calamities (hailstorm, landslide, flood). "
            "Sum insured equals the Scale of Finance set by DLTC (District Level Technical Committee). "
            "Claim process: farmer reports loss within 72 hours via Crop Insurance App, 14447 helpline, or to insurance company/bank/agriculture dept. "
            "Crop cutting experiments (CCE) determine yield loss at village level. "
            "Claim payment via DBT to bank account. "
            "RWBCIS (Restructured Weather Based Crop Insurance Scheme) is a companion scheme based on weather parameters instead of yield. "
            "Both schemes are voluntary for non-loanee farmers from Kharif 2020 onwards."
        ),
    },
    {
        "id": "kcc",
        "name": "Kisan Credit Card",
        "name_hi": "किसान क्रेडिट कार्ड",
        "tagline": "Flexible crop loans at 4% interest",
        "tagline_hi": "4% ब्याज पर लचीला फसल ऋण",
        "category": "Credit & Loans",
        "category_hi": "ऋण व क्रेडिट",
        "icon": "💳",
        "color": "#7c3aed",
        "description": (
            "Kisan Credit Card (KCC) provides farmers with affordable and timely credit for their agricultural needs. "
            "With interest subvention, the effective interest rate is just 4% per annum for loans up to ₹3 lakh "
            "when repaid on time. The card works like a revolving credit facility."
        ),
        "description_hi": (
            "किसान क्रेडिट कार्ड किसानों को कृषि जरूरतों के लिए सस्ता और समय पर ऋण देता है। "
            "ब्याज सब्सिडी के साथ ₹3 लाख तक के ऋण पर प्रभावी ब्याज दर मात्र 4% प्रति वर्ष है।"
        ),
        "benefits": [
            "Crop loan at 4% effective interest rate (up to ₹3 lakh, on-time repayment)",
            "Covers crop cultivation, post-harvest expenses, farm maintenance",
            "Also covers allied activities: animal husbandry, fisheries",
            "Revolving credit — withdraw and repay as needed",
            "Accident insurance of ₹50,000 included",
            "No collateral required up to ₹1.6 lakh",
        ],
        "benefits_hi": [
            "₹3 लाख तक 4% प्रभावी ब्याज पर फसल ऋण",
            "फसल उत्पादन, कटाई के बाद खर्च, खेत रखरखाव कवर",
            "पशुपालन, मछली पालन के लिए भी",
            "रिवॉल्विंग क्रेडिट — जरूरत के हिसाब से निकालें",
            "₹50,000 का दुर्घटना बीमा शामिल",
            "₹1.6 लाख तक कोई गिरवी नहीं",
        ],
        "eligibility": [
            "All farmers — individual, joint borrowers, tenant farmers, sharecroppers",
            "SHG / Joint Liability Group members engaged in farming",
            "Minimum age: 18 years",
            "Land records required for crop loan",
        ],
        "eligibility_hi": [
            "सभी किसान — व्यक्तिगत, संयुक्त, किरायेदार, बटाईदार",
            "खेती में लगे SHG / संयुक्त देयता समूह के सदस्य",
            "न्यूनतम आयु: 18 वर्ष",
            "फसल ऋण के लिए जमीन के कागज जरूरी",
        ],
        "how_to_apply": [
            "Visit nearest bank branch (any commercial bank, RRB, cooperative bank)",
            "Submit application with land records, Aadhaar, passport photo",
            "Bank assesses credit limit based on land holding and crop",
            "Card issued within 2 weeks; valid for 5 years with annual review",
        ],
        "how_to_apply_hi": [
            "नजदीकी बैंक शाखा में जाएं (कमर्शियल बैंक, RRB, सहकारी बैंक)",
            "जमीन के कागज, आधार, फोटो के साथ आवेदन दें",
            "बैंक जमीन और फसल के आधार पर क्रेडिट सीमा तय करेगा",
            "2 सप्ताह में कार्ड मिलेगा; 5 साल के लिए मान्य",
        ],
        "documents": ["Aadhaar Card", "Land Records", "Passport Photo", "Bank Account Details"],
        "official_link": "https://www.nabard.org/content1.aspx?id=572",
        "ai_context": (
            "Kisan Credit Card (KCC) scheme started in 1998–99 by NABARD. "
            "Credit limit calculated as: (Crop cultivation cost × area + 10% for post-harvest/maintenance + 20% for farm asset maintenance + crop insurance premium + consumption requirements) for short-term credit. "
            "Interest subvention: GoI provides 2% subvention to banks + 3% incentive for prompt repayment → effective rate 4% for loans up to ₹3 lakh. "
            "For loans above ₹3 lakh, normal bank rate applies (typically 7–9%). "
            "KCC also covers term loans for allied activities (up to ₹2 lakh for fishermen, ₹2 lakh for animal husbandry). "
            "Repayment period: aligned with crop harvest + marketing period (typically 12 months). "
            "No processing fee on KCC up to ₹3 lakh. "
            "PMFBY insurance is typically bundled with KCC. "
            "ATM-enabled RuPay KCC card allows cash withdrawal and POS payments. "
            "Helpline: 1800-180-1551 (NABARD)."
        ),
    },
    {
        "id": "pmksy",
        "name": "PM Krishi Sinchai Yojana",
        "name_hi": "पीएम कृषि सिंचाई योजना",
        "tagline": "Har Khet Ko Pani, More Crop Per Drop",
        "tagline_hi": "हर खेत को पानी, हर बूँद से अधिक फसल",
        "category": "Irrigation",
        "category_hi": "सिंचाई",
        "icon": "💧",
        "color": "#0891b2",
        "description": (
            "PM Krishi Sinchai Yojana (PMKSY) aims to ensure water to every farm field and improve water use efficiency. "
            "Under 'Per Drop More Crop', it provides 55% subsidy (45% for large farmers) on micro-irrigation systems "
            "like drip and sprinkler irrigation."
        ),
        "description_hi": (
            "PMKSY का लक्ष्य हर खेत तक पानी पहुंचाना और पानी की उपयोग दक्षता सुधारना है। "
            "'हर बूँद से अधिक फसल' के तहत ड्रिप और स्प्रिंकलर सिंचाई पर छोटे किसानों को 55% सब्सिडी मिलती है।"
        ),
        "benefits": [
            "55% subsidy on drip/sprinkler irrigation for small & marginal farmers",
            "45% subsidy for other farmers",
            "Reduces water consumption by 40–50%",
            "Increases crop yield by 40–50%",
            "Covers installation cost of entire micro-irrigation system",
        ],
        "benefits_hi": [
            "छोटे व सीमांत किसानों को ड्रिप/स्प्रिंकलर पर 55% सब्सिडी",
            "अन्य किसानों को 45% सब्सिडी",
            "पानी की खपत 40–50% कम",
            "फसल उत्पादन 40–50% बढ़ता है",
            "पूरे माइक्रो-इरिगेशन सिस्टम की लागत कवर",
        ],
        "eligibility": [
            "All categories of farmers with own land",
            "Tenant farmers with at least 7 years lease agreement",
            "SHGs, cooperative societies, and FPOs also eligible",
            "Priority to small & marginal farmers (< 2 hectares)",
        ],
        "eligibility_hi": [
            "अपनी जमीन वाले सभी किसान",
            "7 साल के पट्टे वाले किरायेदार किसान",
            "SHG, सहकारी समितियां और FPO भी पात्र",
            "छोटे व सीमांत किसानों को प्राथमिकता",
        ],
        "how_to_apply": [
            "Apply at state agriculture department or district collector office",
            "Register on respective state's PMKSY portal",
            "Technical inspection of land done before approval",
            "Subsidy released after installation verification by Agriculture Officer",
        ],
        "how_to_apply_hi": [
            "राज्य कृषि विभाग या जिला कलेक्टर कार्यालय में आवेदन करें",
            "राज्य के PMKSY पोर्टल पर पंजीकरण करें",
            "अनुमोदन से पहले जमीन का तकनीकी निरीक्षण होगा",
            "कृषि अधिकारी की जांच के बाद सब्सिडी जारी होगी",
        ],
        "documents": ["Aadhaar Card", "Land Records", "Bank Passbook", "Caste Certificate (if applicable)"],
        "official_link": "https://pmksy.gov.in",
        "ai_context": (
            "PMKSY has 4 components: Accelerated Irrigation Benefit Programme (AIBP), Har Khet Ko Pani (HKKP), "
            "Per Drop More Crop (PDMC), and Watershed Development. "
            "PDMC subsidy: 55% for small/marginal farmers, 45% for others (states may top-up). "
            "Eligible systems: drip irrigation, micro-sprinkler, mini-sprinkler, portable sprinkler. "
            "Implementation: beneficiary selects empanelled manufacturer from state list, pays their share upfront, "
            "then subsidy is credited to bank account post-verification. "
            "District-wise implementation by PMKSY District Irrigation Plan. "
            "Goal: expand micro-irrigation coverage, reduce water footprint of agriculture, and help in water-stressed areas. "
            "Average payback period for drip system: 3–4 years from crop yield increase and water savings."
        ),
    },
    {
        "id": "enam",
        "name": "e-NAM",
        "name_hi": "ई-नाम",
        "tagline": "Sell your crop online to the best buyer",
        "tagline_hi": "ऑनलाइन बेचें — सबसे अच्छे खरीदार को",
        "category": "Market Access",
        "category_hi": "बाज़ार पहुंच",
        "icon": "🏪",
        "color": "#d97706",
        "description": (
            "National Agriculture Market (e-NAM) is an online trading platform for agricultural commodities. "
            "It connects APMC mandis across India, enabling farmers to get the best price through transparent "
            "online bidding without having to physically visit distant markets."
        ),
        "description_hi": (
            "राष्ट्रीय कृषि बाज़ार (e-NAM) कृषि वस्तुओं के लिए एक ऑनलाइन ट्रेडिंग प्लेटफॉर्म है। "
            "यह पूरे भारत की APMC मंडियों को जोड़ता है, जिससे किसान पारदर्शी ऑनलाइन बोली के जरिए "
            "बेहतर दाम पा सकते हैं।"
        ),
        "benefits": [
            "Access to buyers across India — not just local traders",
            "Transparent price discovery through online bidding",
            "Online payment directly to farmer's bank account",
            "Quality assaying at the mandi before bidding",
            "Reduced market fees and better price realisation",
        ],
        "benefits_hi": [
            "पूरे भारत के खरीदारों तक पहुंच",
            "ऑनलाइन बोली से पारदर्शी मूल्य खोज",
            "सीधे बैंक खाते में ऑनलाइन भुगतान",
            "बोली से पहले मंडी में गुणवत्ता जांच",
            "कम बाज़ार शुल्क और बेहतर दाम",
        ],
        "eligibility": [
            "Any farmer registered with their local APMC mandi",
            "Registration on enam.gov.in with Aadhaar and bank account",
            "Commodity must be on the e-NAM notified list",
        ],
        "eligibility_hi": [
            "स्थानीय APMC मंडी में पंजीकृत कोई भी किसान",
            "enam.gov.in पर आधार और बैंक खाते से पंजीकरण",
            "फसल e-NAM अधिसूचित सूची में होनी चाहिए",
        ],
        "how_to_apply": [
            "Register at enam.gov.in or at the local e-NAM integrated mandi",
            "Get Farmer ID from the mandi gate-keeper at the time of produce arrival",
            "Produce is weighed, assayed for quality, then put up for online bidding",
            "Highest bid accepted; payment within 2 working days to bank account",
        ],
        "how_to_apply_hi": [
            "enam.gov.in पर या e-NAM एकीकृत मंडी में पंजीकरण करें",
            "उपज लाते समय मंडी गेट पर किसान ID लें",
            "उपज की तौल और गुणवत्ता जांच होगी, फिर ऑनलाइन बोली",
            "सबसे ऊंची बोली स्वीकार; 2 कार्यदिवस में भुगतान",
        ],
        "documents": ["Aadhaar Card", "Bank Passbook", "Mobile Number", "APMC Registration"],
        "official_link": "https://enam.gov.in",
        "ai_context": (
            "e-NAM (National Agriculture Market) launched in April 2016 by SFAC (Small Farmers Agribusiness Consortium) under MoA&FW. "
            "As of 2024, over 1,361 mandis across 23 states and 3 UTs are integrated. "
            "Commodities covered: 175+ including cereals, pulses, oilseeds, fibre, vegetables, fruits, spices. "
            "Farmer registration: free, done at the mandi or online. "
            "Trading modes: within mandi bidding, inter-mandi trading, FPO trading, warehouse-based trading. "
            "Assaying: quality tested by mandi-appointed assayer; grade & price displayed for bidding. "
            "Payment: through e-NAM payment gateway, directly credited to farmer's Aadhaar-linked account. "
            "Mobile app: e-NAM app available for Android (farmers can see prices, bids, payment status). "
            "Helpline: 1800-270-0224. "
            "Key benefit: eliminates the need to physically travel to a distant large mandi; can sell from local mandi at best national price."
        ),
    },
    {
        "id": "soil-health-card",
        "name": "Soil Health Card",
        "name_hi": "मृदा स्वास्थ्य कार्ड",
        "tagline": "Know your soil, grow smarter",
        "tagline_hi": "अपनी मिट्टी जानें, बेहतर खेती करें",
        "category": "Soil & Inputs",
        "category_hi": "मृदा व आदान",
        "icon": "🌱",
        "color": "#65a30d",
        "description": (
            "The Soil Health Card Scheme provides every farmer a Soil Health Card every two years "
            "with information on their soil's nutrient status and recommendations on appropriate fertilizer "
            "dosages to improve soil health and crop productivity."
        ),
        "description_hi": (
            "मृदा स्वास्थ्य कार्ड योजना हर किसान को हर दो साल में एक मृदा स्वास्थ्य कार्ड देती है "
            "जिसमें मिट्टी की पोषक स्थिति और सही उर्वरक खुराक की जानकारी होती है।"
        ),
        "benefits": [
            "Free soil testing for 12 parameters (N, P, K, pH, micronutrients etc.)",
            "Personalized fertilizer recommendation for each crop",
            "Reduces fertilizer cost by 8–10% through optimal use",
            "Improves yield by 5–6% through correct nutrient management",
            "Card valid for 2 years",
        ],
        "benefits_hi": [
            "12 मापदंडों की मुफ्त मिट्टी जांच",
            "हर फसल के लिए व्यक्तिगत उर्वरक सिफारिश",
            "सही उपयोग से उर्वरक लागत 8–10% कम",
            "सही पोषण से उपज 5–6% बढ़ती है",
            "कार्ड 2 साल के लिए मान्य",
        ],
        "eligibility": [
            "All farmers in India — no restrictions",
            "Applicable for all crops and land types",
        ],
        "eligibility_hi": [
            "भारत के सभी किसान — कोई प्रतिबंध नहीं",
            "सभी फसलों और जमीन के प्रकार पर लागू",
        ],
        "how_to_apply": [
            "Contact local Agriculture Department or Krishi Vigyan Kendra (KVK)",
            "Soil sampling done by Agriculture Department staff from your field",
            "Card issued within 2–3 months with crop-wise fertilizer dosage",
            "Check card status at soilhealth.dac.gov.in",
        ],
        "how_to_apply_hi": [
            "स्थानीय कृषि विभाग या KVK से संपर्क करें",
            "कृषि विभाग के कर्मचारी खेत से मिट्टी का नमूना लेंगे",
            "2–3 महीने में फसलवार उर्वरक खुराक के साथ कार्ड मिलेगा",
            "soilhealth.dac.gov.in पर कार्ड की स्थिति देखें",
        ],
        "documents": ["Aadhaar Card", "Land Details (village, survey number)", "Mobile Number"],
        "official_link": "https://soilhealth.dac.gov.in",
        "ai_context": (
            "Soil Health Card (SHC) scheme launched in February 2015 under Department of Agriculture, Cooperation & Farmers' Welfare. "
            "Testing parameters: 12 — N (Nitrogen), P (Phosphorus), K (Potassium), S (Sulphur), Zn (Zinc), B (Boron), Fe (Iron), Mn (Manganese), Cu (Copper), pH, EC (Electrical Conductivity), OC (Organic Carbon). "
            "Sampling cycle: once every 2 years (irrigated areas), once every 3 years (rainfed/hilly areas). "
            "The card recommends fertilizer dosage for 6 crops based on soil test results and target yield. "
            "Micronutrient deficiency is a major problem — zinc deficiency affects 49% of Indian soils. "
            "SHC helps farmers avoid over-application of urea (common problem) and use secondary/micro nutrients properly. "
            "Soil testing labs: ~2,500+ static labs and mobile labs across India. "
            "The recommendation is customized per village/block, not just per state. "
            "Farmers should bring their SHC to the fertilizer shop to buy the right fertilizers."
        ),
    },
    {
        "id": "pkvy",
        "name": "Paramparagat Krishi Vikas Yojana",
        "name_hi": "परम्परागत कृषि विकास योजना",
        "tagline": "Organic farming support — ₹50,000/hectare",
        "tagline_hi": "जैविक खेती सहायता — ₹50,000/हेक्टेयर",
        "category": "Organic Farming",
        "category_hi": "जैविक खेती",
        "icon": "🌿",
        "color": "#059669",
        "description": (
            "Paramparagat Krishi Vikas Yojana (PKVY) promotes organic farming in India through financial "
            "support to farmer groups. Farmers get ₹50,000 per hectare over 3 years for cluster-based "
            "organic farming, certification, and market linkages."
        ),
        "description_hi": (
            "PKVY किसान समूहों को वित्तीय सहायता के माध्यम से जैविक खेती को बढ़ावा देती है। "
            "किसानों को क्लस्टर-आधारित जैविक खेती, प्रमाणन और बाज़ार जुड़ाव के लिए "
            "3 साल में ₹50,000 प्रति हेक्टेयर मिलता है।"
        ),
        "benefits": [
            "₹50,000/hectare over 3 years (₹31,000 to farmer, rest for certification & marketing)",
            "Free organic certification (PGS-India system)",
            "Support for bio-inputs: vermicompost, biofertilizers, botanical pesticides",
            "Market linkage support and branding",
            "Premium price for certified organic produce",
        ],
        "benefits_hi": [
            "3 साल में ₹50,000/हेक्टेयर (₹31,000 किसान को, बाकी प्रमाणन व मार्केटिंग)",
            "मुफ्त जैविक प्रमाणन (PGS-India)",
            "जैव आदान: वर्मीकम्पोस्ट, जैव उर्वरक, वनस्पति कीटनाशक",
            "बाज़ार जुड़ाव और ब्रांडिंग सहायता",
            "प्रमाणित जैविक उत्पाद को प्रीमियम मूल्य",
        ],
        "eligibility": [
            "Farmers must form a cluster of minimum 20 hectares (50 farmers)",
            "Cluster approach — individual farmers cannot apply alone",
            "Preference to regions with low chemical use",
            "Commitment to 3-year organic conversion",
        ],
        "eligibility_hi": [
            "न्यूनतम 20 हेक्टेयर (50 किसान) का क्लस्टर बनाना जरूरी",
            "व्यक्तिगत किसान अकेले आवेदन नहीं कर सकते",
            "कम रासायनिक उपयोग वाले क्षेत्रों को प्राथमिकता",
            "3 वर्षीय जैविक रूपांतरण की प्रतिबद्धता",
        ],
        "how_to_apply": [
            "Form a group of 50+ farmers with 20+ hectares of contiguous land",
            "Apply through local Agriculture Department / Atma (Agricultural Technology Management Agency)",
            "Cluster Lead Resource Person (CLRP) assigned to guide the group",
            "Annual funding released in 3 tranches over 3 years",
        ],
        "how_to_apply_hi": [
            "20+ हेक्टेयर की सटी जमीन वाले 50+ किसानों का समूह बनाएं",
            "स्थानीय कृषि विभाग / ATMA के माध्यम से आवेदन करें",
            "मार्गदर्शन के लिए क्लस्टर लीड रिसोर्स पर्सन (CLRP) नियुक्त होगा",
            "3 साल में 3 किस्तों में वार्षिक फंडिंग",
        ],
        "documents": ["Aadhaar Card", "Land Records", "Group Formation Document", "Bank Account (group/individual)"],
        "official_link": "https://pgsindia-ncof.gov.in",
        "ai_context": (
            "PKVY (Paramparagat Krishi Vikas Yojana) launched in 2015 under National Mission for Sustainable Agriculture (NMSA). "
            "Financial assistance: ₹50,000/ha over 3 years — ₹10,000 for cluster formation/capacity building, "
            "₹31,000 for bio-inputs (year-wise: ₹15,000, ₹10,000, ₹6,000), ₹8,000 for value addition/packaging/marketing, ₹1,000 for PGS certification. "
            "PGS-India (Participatory Guarantee System) is a decentralised, participatory organic certification — cheaper than third-party certification. "
            "The scheme emphasizes on-farm composting, use of traditional seeds, and local bio-inputs rather than purchased inputs. "
            "Companion scheme: Mission Organic Value Chain Development for North Eastern Region (MOVCDNER). "
            "Organic clusters produce must be sold under the Jaivik Kheti brand or direct marketing through organic fairs. "
            "Farmers can also list their produce on Jaivik Kheti portal (jaivikkheti.in)."
        ),
    },
    {
        "id": "rkvy",
        "name": "RKVY-RAFTAAR",
        "name_hi": "RKVY-रफ्तार",
        "tagline": "Agriculture infrastructure & startup funding",
        "tagline_hi": "कृषि अवसंरचना और स्टार्टअप फंडिंग",
        "category": "Infrastructure",
        "category_hi": "अवसंरचना",
        "icon": "🏗️",
        "color": "#dc2626",
        "description": (
            "Rashtriya Krishi Vikas Yojana – RAFTAAR supports agriculture and allied sectors through "
            "infrastructure investment, value chain development, and agri-startup funding. "
            "It provides grants for cold storage, processing units, and agri-tech entrepreneurs."
        ),
        "description_hi": (
            "RKVY-RAFTAAR बुनियादी ढांचे, मूल्य श्रृंखला विकास और कृषि स्टार्टअप फंडिंग के माध्यम से "
            "कृषि और संबद्ध क्षेत्रों को समर्थन देती है।"
        ),
        "benefits": [
            "Funding for cold storage, food processing, warehousing",
            "Agri-startup grants: up to ₹25 lakh seed funding",
            "Incubation support for agri-entrepreneurs",
            "State-level flexibility for project selection",
            "Value chain and cluster development support",
        ],
        "benefits_hi": [
            "कोल्ड स्टोरेज, फूड प्रोसेसिंग, गोदाम के लिए फंडिंग",
            "कृषि स्टार्टअप को ₹25 लाख तक सीड फंडिंग",
            "कृषि उद्यमियों के लिए इन्क्यूबेशन सहायता",
            "परियोजना चयन में राज्य स्तरीय लचीलापन",
            "मूल्य श्रृंखला और क्लस्टर विकास",
        ],
        "eligibility": [
            "State governments apply on behalf of implementing agencies",
            "FPOs, cooperatives, agri-startups can apply through RKVY-RAFTAAR incubators",
            "Individual farmers for specific district/state level projects",
        ],
        "eligibility_hi": [
            "राज्य सरकारें कार्यान्वयन एजेंसियों की ओर से आवेदन करती हैं",
            "FPO, सहकारी समितियां, कृषि स्टार्टअप RKVY इन्क्यूबेटर के माध्यम से",
            "विशिष्ट जिला/राज्य स्तरीय परियोजनाओं के लिए व्यक्तिगत किसान",
        ],
        "how_to_apply": [
            "Agri-startups: apply through RKVY-RAFTAAR incubators (R-ABI) listed on rkvy.nic.in",
            "State-level projects: State Agriculture Department prepares DPR and submits to DARE/ICAR",
            "FPOs: apply through ATMA or State FPO promotion agency",
        ],
        "how_to_apply_hi": [
            "कृषि स्टार्टअप: rkvy.nic.in पर RKVY-RAFTAAR इन्क्यूबेटर के माध्यम से आवेदन",
            "राज्य परियोजनाएं: राज्य कृषि विभाग DPR बनाकर DARE/ICAR को भेजेगा",
            "FPO: ATMA या राज्य FPO प्रोत्साहन एजेंसी के माध्यम से",
        ],
        "documents": ["Business Plan", "Aadhaar/PAN", "Land/Lease Documents", "Bank Account Details"],
        "official_link": "https://rkvy.nic.in",
        "ai_context": (
            "RKVY (Rashtriya Krishi Vikas Yojana) started in 2007; revamped as RKVY-RAFTAAR (Remunerative Approaches for Agriculture and Allied Sector Rejuvenation) in 2017. "
            "Three funding streams: (1) Infrastructure & Assets — warehouses, cold chains, processing units; "
            "(2) Value Chain Development — from farm to market for specific commodities; "
            "(3) Innovation & Agri-entrepreneur — RAFTAAR component: agri-startup incubation. "
            "RAFTAAR provides: pre-incubation training (2 months, stipend ₹10,000/month), incubation (1 year, grant up to ₹5 lakh), "
            "post-incubation seed funding up to ₹25 lakh (60% grant, 40% loan). "
            "R-ABI (RKVY-RAFTAAR Agribusiness Incubators): 24 premier institutes including IITs, MANAGE, NIAM, SAUs. "
            "Focus areas: precision farming, supply chain tech, post-harvest management, agri-drone, fintech for farmers. "
            "State allocation: 60:40 central:state funding ratio (90:10 for NE states)."
        ),
    },
]


def get_all_schemes() -> list[dict]:
    return SCHEMES


def get_scheme_by_id(scheme_id: str) -> dict | None:
    return next((s for s in SCHEMES if s["id"] == scheme_id), None)


def get_categories() -> list[str]:
    seen = []
    for s in SCHEMES:
        if s["category"] not in seen:
            seen.append(s["category"])
    return seen
