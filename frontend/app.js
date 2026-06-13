/* ============================================================
   PICKMYSEAT.AI — app.js
   Grade 3: guest, 1 college, 1 course, 1 prediction (cookie)
   Grade 2: registered, 5 colleges, 3 courses, marks locked
   Grade 1: premium, ANY college search + all features + ₹25 mark update
   ============================================================ */

'use strict';
const API_BASE = 'https://tneapredictor-production.up.railway.app';
// ============================================================
// STATE
// ============================================================
const App = {
  currentPage:     'landing',
  currentUser:     null,
  userGrade:       3,
  liveCount:       parseInt(localStorage.getItem('pms_live_count') || '300'),
  slotsLeft:       23,
  rankPhase:       'pre',
  counsellingStep: 0,
  theme:           'dark',
  simStep:         0,
  simChoices:      [],
  simAllotment:    null,
  simFilter:       { college: '', branch: '', category: '' },

  profile: {
    name:              '',
    email:             '',
    mobile:            '',
    category:          '',
    maths:             null,
    physics:           null,
    chemistry:         null,
    marksLocked:       false,
    rank:              null,
    rankPhase:         'pre',
    hasPaid:           false,
    preferredColleges: [],
    preferredCourses:  [],
  }
};

// ============================================================
// FULL COLLEGE LIST — all 550 colleges with codes
// ============================================================
let COLLEGES = [
  { code:'0001', name:'University Departments of Anna University - CEG Campus' },
  { code:'0002', name:'University Departments of Anna University - ACT Campus' },
  { code:'0003', name:'University Departments of Anna University - SAP Campus' },
  { code:'0004', name:'University Departments of Anna University - MIT Campus' },
  { code:'0005', name:'Annamalai University Faculty of Engineering' },
  { code:'1516', name:'Thanthai Periyar Government Institute of Technology' },
  { code:'2005', name:'Government College of Technology (Autonomous), Coimbatore' },
  { code:'2369', name:'Government College of Engineering, Dharmapuri' },
  { code:'2603', name:'Government College of Engineering (Autonomous), Bargur' },
  { code:'2615', name:'Government College of Engineering (Autonomous), Salem' },
  { code:'2709', name:'Government Engineering College, Erode' },
  { code:'3464', name:'Government College of Engineering, Gandarvakottai Road' },
  { code:'3465', name:'Government College of Engineering, Srirangam' },
  { code:'4974', name:'Government College of Engineering, Tirunelveli' },
  { code:'5009', name:'Government College of Engineering, Melachokkanathapuram' },
  { code:'5901', name:'Alagappa Chettiar Government College of Engineering, Karaikudi' },
  { code:'2006', name:'PSG College of Technology (Autonomous), Coimbatore' },
  { code:'2007', name:'Coimbatore Institute of Technology (Autonomous)' },
  { code:'5008', name:'Thiagarajar College of Engineering, Madurai' },
  { code:'1321', name:'Central Institute of Plastics Engineering and Technology (CIPET)' },
  { code:'2343', name:'Indian Institute of Handloom Technology' },
  { code:'5012', name:'Central Electrochemical Research Institute (CECRI), Karaikudi' },
  { code:'1013', name:'University College of Engineering, Villupuram' },
  { code:'1014', name:'University College of Engineering, Tindivanam' },
  { code:'1015', name:'University College of Engineering, Arni' },
  { code:'1026', name:'University College of Engineering, Kancheepuram' },
  { code:'2025', name:'Anna University Regional Campus - Coimbatore' },
  { code:'3011', name:'University College of Engineering, Tiruchirappalli' },
  { code:'3016', name:'University College of Engineering, Ariyalur' },
  { code:'3018', name:'University College of Engineering, Thirukkuvalai' },
  { code:'3019', name:'University College of Engineering, Panruti' },
  { code:'3021', name:'University College of Engineering, Pattukkottai' },
  { code:'4020', name:'Anna University Regional Campus - Tirunelveli' },
  { code:'4023', name:'University College of Engineering, Nagercoil' },
  { code:'4024', name:'University V.O.C. College of Engineering, Thoothukudi' },
  { code:'5010', name:'Anna University Regional Campus - Madurai' },
  { code:'5017', name:'University College of Engineering, Ramanathapuram' },
  { code:'5022', name:'University College of Engineering, Dindigul' },
  { code:'1101', name:'Aalim Muhammed Salegh College of Engineering' },
  { code:'1106', name:'Jaya Engineering College, Thirunindravur' },
  { code:'1107', name:'Jaya Institute of Technology, Thiruvallur' },
  { code:'1110', name:'Prathyusha Engineering College, Thiruvallur' },
  { code:'1112', name:'R M D Engineering College, Gummidipoondi' },
  { code:'1113', name:'R M K Engineering College (Autonomous), Kavaraipettai' },
  { code:'1114', name:'S A Engineering College (Autonomous), Chennai' },
  { code:'1115', name:'Sri Ram Engineering College, Veppampattu' },
  { code:'1116', name:'Sri Venkateswara College of Engineering and Technology' },
  { code:'1118', name:'Vel Tech Multi Tech Dr. Rangarajan Dr. Sakunthala Engineering' },
  { code:'1120', name:'Velammal Engineering College (Autonomous), Ambattur' },
  { code:'1122', name:'Vel Tech High Tech Dr. Rangarajan Dr. Sakunthala Engineering' },
  { code:'1123', name:'Gojan School of Business and Technology, Chennai' },
  { code:'1124', name:'SAMS College of Engineering and Technology' },
  { code:'1125', name:'P M R Engineering College, Maduravoyal' },
  { code:'1126', name:'J N N Institute of Engineering, Kannigaipair Village' },
  { code:'1127', name:'St. Peters College of Engineering and Technology' },
  { code:'1128', name:'R M K College of Engineering and Technology, Puduvoyal' },
  { code:'1133', name:'Annai Veilankannis College of Engineering' },
  { code:'1137', name:'Annai Mira College of Engineering and Technology' },
  { code:'1140', name:'Jeppiaar Institute of Technology, Sriperumpudur' },
  { code:'1149', name:'St. Josephs Institute of Technology, Chennai' },
  { code:'1150', name:'Sri Jayaram Institute of Engineering and Technology' },
  { code:'1202', name:'D M I College of Engineering, Chennai' },
  { code:'1205', name:'Lord Venkateshwara Engineering College, Walajabad' },
  { code:'1207', name:'Kings Engineering College, Sriperumpudur' },
  { code:'1209', name:'Pallavan College of Engineering, Kancheepuram' },
  { code:'1210', name:'Panimalar Engineering College, Poonamallee' },
  { code:'1211', name:'Rajalakshmi Engineering College (Autonomous), Thandalam' },
  { code:'1212', name:'Rajiv Gandhi College of Engineering, Sriperumpudur' },
  { code:'1216', name:'Saveetha Engineering College (Autonomous), Thandalam' },
  { code:'1217', name:'Sree Sastha Institute of Engineering and Technology' },
  { code:'1218', name:'Sri Muthukumaran Institute of Technology, Chennai' },
  { code:'1219', name:'Sri Venkateswara College of Engineering (Autonomous)' },
  { code:'1221', name:'Jaya College of Engineering and Technology, Parivakkam' },
  { code:'1222', name:'P B College of Engineering, Sriperumpudur' },
  { code:'1225', name:'Loyola Institute of Technology, Mevaloorkuppam' },
  { code:'1226', name:'P T Lee Chengalvaraya Naicker College of Engineering' },
  { code:'1228', name:'Alpha College of Engineering' },
  { code:'1229', name:'Indira Institute of Engineering and Technology' },
  { code:'1230', name:'Apollo Engineering College, Mevaloorkuppam' },
  { code:'1231', name:'Panimalar Institute of Technology, Poonamallee' },
  { code:'1233', name:'Adhi College of Engineering and Technology' },
  { code:'1235', name:'JEI Mathaajee College of Engineering' },
  { code:'1237', name:'Velammal Institute of Technology, Chennai' },
  { code:'1238', name:'GRT Institute of Engineering and Technology' },
  { code:'1241', name:'T J S Engineering College, Kavaraipettai' },
  { code:'1243', name:'Madha Institute of Engineering and Technology' },
  { code:'1301', name:'Mohamed Sathak A J College of Engineering' },
  { code:'1303', name:'Anand Institute of Higher Technology, OMR' },
  { code:'1304', name:'Easwari Engineering College (Autonomous), Ramapuram' },
  { code:'1306', name:'Jeppiar Engineering College, OMR Chennai' },
  { code:'1307', name:'Jerusalem College of Engineering (Autonomous)' },
  { code:'1309', name:'Meenakshi Sundararajan Engineering College' },
  { code:'1310', name:'Misrimal Navajee Munoth Jain Engineering College' },
  { code:'1311', name:'K C G College of Technology, Chennai' },
  { code:'1313', name:'Shree Motilal Kanhaiyalal Fomra Institute of Technology' },
  { code:'1315', name:'Sri Sivasubramaniya Nadar College of Engineering (Autonomous)' },
  { code:'1316', name:'Agni College of Technology, OMR Chennai' },
  { code:'1317', name:'St. Josephs College of Engineering, OMR Chennai' },
  { code:'1318', name:'T.J Institute of Technology, Karapakkam' },
  { code:'1319', name:'Thangavelu Engineering College, Karappakkam' },
  { code:'1322', name:'Dhanalakshmi Srinivasan College of Engineering and Technology' },
  { code:'1324', name:'Sri Sai Ram Institute of Technology (Autonomous), Tambaram' },
  { code:'1325', name:'St. Joseph College of Engineering, Nemili' },
  { code:'1333', name:'Vi Institute of Technology, Sirunkundram Village' },
  { code:'1335', name:'Sri Krishna Institute of Technology, Padappai' },
  { code:'1399', name:'Chennai Institute of Technology, Nandambakkam' },
  { code:'1401', name:'Adhiparasakthi Engineering College, Melmaruvathur' },
  { code:'1402', name:'Annai Terasa College of Engineering, Kallakkurichi' },
  { code:'1405', name:'Dhanalakshmi College of Engineering, Manimangalam' },
  { code:'1407', name:'G K M College of Engineering and Technology' },
  { code:'1408', name:'I F E T College of Engineering (Autonomous)' },
  { code:'1409', name:'Karpagavinayaga College of Engineering and Technology' },
  { code:'1411', name:'Madha Engineering College, Kundrathur' },
  { code:'1412', name:'Mailam Engineering College, Villupuram' },
  { code:'1413', name:'Sri Venkateswaraa College of Technology, Vadakkal' },
  { code:'1414', name:'Prince Shri Venkateshwara Padmavathy Engineering College' },
  { code:'1415', name:'T S M Jain College of Technology, Kallakurichi' },
  { code:'1416', name:'Jaya Sakthi Engineering College, Thirunindravur' },
  { code:'1419', name:'Sri Sairam Engineering College (Autonomous), Tambaram' },
  { code:'1420', name:'Tagore Engineering College, Vandalur' },
  { code:'1421', name:'V R S College of Engineering and Technology, Villupuram' },
  { code:'1422', name:'SRM Valliammai Engineering College (Autonomous), Kattankulathur' },
  { code:'1423', name:'Asan Memorial College of Engineering' },
  { code:'1424', name:'Dhaanish Ahmed College of Engineering, Padappai' },
  { code:'1426', name:'Sri Ramanujar Engineering College, Vandalur' },
  { code:'1427', name:'Sri Krishna Engineering College, Padappai' },
  { code:'1430', name:'Maha Bharathi Engineering College, Chinnasalem' },
  { code:'1431', name:'New Prince Shri Bhavani College of Engineering and Technology' },
  { code:'1432', name:'Rajalakshmi Institute of Technology, Kuthampakkam' },
  { code:'1434', name:'Surya Group of Institutions, Villupuram' },
  { code:'1435', name:'Jagannath Institute of Technology, Thiruporur' },
  { code:'1436', name:'A R Engineering College, Kappiyampuliyur' },
  { code:'1437', name:'Rrase College of Engineering, Padappai' },
  { code:'1438', name:'Sree Krishna College of Engineering, Anaicut' },
  { code:'1441', name:'A K T Memorial College of Engineering and Technology' },
  { code:'1442', name:'Prince Dr. K Vasudevan College of Engineering and Technology' },
  { code:'1444', name:'Chendu College of Engineering and Technology' },
  { code:'1445', name:'Sri Rangapoopathi College of Engineering' },
  { code:'1447', name:'Jawahar Engineering College, Saligramam' },
  { code:'1449', name:'Saraswathy College of Engineering and Technology' },
  { code:'1450', name:'Loyola-ICAM College of Engineering and Technology' },
  { code:'1452', name:'PERI Institute of Technology, Tambaram' },
  { code:'1501', name:'Adhiparasakthi College of Engineering, Kalavai' },
  { code:'1503', name:'Arulmigu Meenakshi Amman College of Engineering' },
  { code:'1504', name:'Arunai Engineering College, Thiruvannamalai' },
  { code:'1505', name:'C Abdul Hakeem College of Engineering and Technology' },
  { code:'1507', name:'Ganadipathy Tulsis Jain Engineering College, Vellore' },
  { code:'1509', name:'Meenakshi College of Engineering, K K Nagar' },
  { code:'1510', name:'Priyadarshini Engineering College, Vaniyambadi' },
  { code:'1511', name:'Ranippettai Engineering College, Ranipet' },
  { code:'1512', name:'S K P Engineering College, Thiruvannamalai' },
  { code:'1513', name:'Sri Balaji Chockalingam Engineering College, Arni' },
  { code:'1517', name:'Thirumalai Engineering College, Kancheepuram' },
  { code:'1518', name:'Thiruvalluvar College of Engineering and Technology, Vandavasi' },
  { code:'1519', name:'Bharathidasan Engineering College, Thiruppathur' },
  { code:'1520', name:'Kingston Engineering College, Christianpet' },
  { code:'1523', name:'Global Institute of Engineering and Technology' },
  { code:'1524', name:'Annamalaiar College of Engineering, Polur' },
  { code:'1525', name:'Podhigai College of Engineering and Technology' },
  { code:'1526', name:'Sri Krishna College of Engineering, Arakkonam' },
  { code:'1529', name:'Oxford College of Engineering, Karaipoondi' },
  { code:'1605', name:'Idhaya Engineering College for Women, Kallakkurichi' },
  { code:'2302', name:'Sri Shanmugha College of Engineering and Technology' },
  { code:'2314', name:'Muthayammal College of Engineering, Namakkal' },
  { code:'2327', name:'N S N College of Engineering and Technology, Karur' },
  { code:'2328', name:'K S R Institute for Engineering and Technology' },
  { code:'2329', name:'Rathinam Technical Campus, Coimbatore' },
  { code:'2332', name:'Aishwarya College of Engineering and Technology' },
  { code:'2338', name:'Asian College of Engineering and Technology, Coimbatore' },
  { code:'2341', name:'Ganesh College of Engineering, Salem' },
  { code:'2342', name:'Sri Ranganathar Institute of Engineering and Technology' },
  { code:'2345', name:'Dhirajlal Gandhi College of Technology, Salem' },
  { code:'2346', name:'Shree Sathyam College of Engineering and Technology' },
  { code:'2347', name:'AVS College of Technology, Salem' },
  { code:'2349', name:'Dhaanish Ahmed Institute of Technology, Coimbatore' },
  { code:'2350', name:'Jairupaa College of Engineering' },
  { code:'2354', name:'Pollachi Institute of Engineering and Technology' },
  { code:'2355', name:'Cheran College of Engineering, Coimbatore' },
  { code:'2356', name:'Arulmurugan College of Engineering' },
  { code:'2357', name:'V S B College of Engineering Technical Campus' },
  { code:'2360', name:'Suguna College of Engineering, Coimbatore' },
  { code:'2367', name:'Arjun College of Technology, Coimbatore' },
  { code:'2377', name:'PSG Institute of Technology and Applied Research, Coimbatore' },
  { code:'2601', name:'Adhiyamaan College of Engineering (Autonomous), Hosur' },
  { code:'2602', name:'Annai Mathammal Sheela Engineering College' },
  { code:'2606', name:'Jayam College of Engineering and Technology, Namakkal' },
  { code:'2607', name:'K S Rangasamy College of Technology (Autonomous), Tiruchengode' },
  { code:'2608', name:'M Kumarasamy College of Engineering (Autonomous)' },
  { code:'2609', name:'Mahendra Engineering College (Autonomous), Namakkal' },
  { code:'2610', name:'Muthayammal Engineering College (Autonomous), Rasipuram' },
  { code:'2611', name:'Paavai Engineering College (Autonomous), Namakkal' },
  { code:'2612', name:'P G P College of Engineering and Technology, Namakkal' },
  { code:'2613', name:'K S R College of Engineering (Autonomous), Tiruchengode' },
  { code:'2614', name:'S S M College of Engineering, Namakkal' },
  { code:'2617', name:'Sengunthar Engineering College (Autonomous), Tiruchengode' },
  { code:'2618', name:'Sona College of Technology (Autonomous), Salem' },
  { code:'2620', name:'Vivekanandha College of Engineering for Women (Autonomous)' },
  { code:'2621', name:'Er. Perumal Manimekalai College of Engineering' },
  { code:'2622', name:'V S B Engineering College, Karur' },
  { code:'2623', name:'Mahendra College of Engineering, Namakkal' },
  { code:'2624', name:'Gnanamani College of Technology, Namakkal' },
  { code:'2625', name:'The Kavery Engineering College, Salem' },
  { code:'2627', name:'Selvam College of Technology, Namakkal' },
  { code:'2628', name:'Paavai College of Engineering, Namakkal' },
  { code:'2629', name:'Sengunthar College of Engineering, Namakkal' },
  { code:'2630', name:'Chettinad College of Engineering and Technology, Trichy' },
  { code:'2632', name:'Mahendra Institute of Technology (Autonomous), Namakkal' },
  { code:'2633', name:'Vidhya Vikkas College of Engineering and Technology' },
  { code:'2634', name:'Excel Engineering College (Autonomous), Namakkal' },
  { code:'2635', name:'C M S College of Engineering, Namakkal' },
  { code:'2636', name:'A V S Engineering College, Salem' },
  { code:'2638', name:'Mahendra Engineering College for Women, Namakkal' },
  { code:'2639', name:'Narasus Sarathy Institute of Technology, Salem' },
  { code:'2640', name:'Jayalakshmi Institute of Technology, Dharmapuri' },
  { code:'2641', name:'Varuvan Vadivelan Institute of Technology, Dharmapuri' },
  { code:'2642', name:'P S V College of Engineering and Technology' },
  { code:'2643', name:'Bharathiyar Institute of Engineering for Women' },
  { code:'2646', name:'Tagore Institute of Engineering and Technology, Salem' },
  { code:'2647', name:'J K K Nataraja College of Engineering and Technology' },
  { code:'2648', name:'Annapoorana Engineering College, Namakkal' },
  { code:'2650', name:'Christ the King Engineering College' },
  { code:'2651', name:'Jai Shriram Engineering College, Tiruppur' },
  { code:'2652', name:'Al-Ameen Engineering College (Autonomous), Coimbatore' },
  { code:'2653', name:'Knowledge Institute of Technology, Salem' },
  { code:'2656', name:'Builders Engineering College, Erode' },
  { code:'2657', name:'Paavai College of Technology, Namakkal' },
  { code:'2658', name:'V S A Group of Institutions, Salem' },
  { code:'2659', name:'Salem College of Engineering and Technology' },
  { code:'2661', name:'Vivekanandha College of Technology for Women' },
  { code:'2662', name:'Dr. Nagarathinams College of Engineering' },
  { code:'2665', name:'Mahendra Institute of Engineering and Technology' },
  { code:'2673', name:'Sree Sakthi Engineering College, Erode' },
  { code:'2683', name:'Shreenivasa Engineering College, Dharmapuri' },
  { code:'2702', name:'Bannari Amman Institute of Technology (Autonomous)' },
  { code:'2704', name:'Coimbatore Institute of Engineering and Technology (Autonomous)' },
  { code:'2705', name:'C S I College of Engineering, Nilgiris' },
  { code:'2706', name:'Dr. Mahalingam College of Engineering and Technology' },
  { code:'2707', name:'Erode Sengunthar Engineering College (Autonomous)' },
  { code:'2708', name:'Hindusthan College of Engineering and Technology (Autonomous)' },
  { code:'2710', name:'Karpagam College of Engineering (Autonomous), Coimbatore' },
  { code:'2711', name:'Kongu Engineering College (Autonomous), Erode' },
  { code:'2712', name:'Kumaraguru College of Technology (Autonomous), Coimbatore' },
  { code:'2713', name:'M P Nachimuthu M Jagannathan Engineering College' },
  { code:'2715', name:'Nandha Engineering College (Autonomous), Erode' },
  { code:'2716', name:'Park College of Engineering and Technology, Coimbatore' },
  { code:'2717', name:'Sasurie College of Engineering, Tiruppur' },
  { code:'2718', name:'Sri Krishna College of Engineering and Technology (Autonomous), Coimbatore' },
  { code:'2719', name:'Sri Ramakrishna Engineering College (Autonomous), Coimbatore' },
  { code:'2721', name:'Tamilnadu College of Engineering, Coimbatore' },
  { code:'2722', name:'Sri Krishna College of Technology (Autonomous), Coimbatore' },
  { code:'2723', name:'Velalar College of Engineering and Technology (Autonomous)' },
  { code:'2725', name:'Sri Ramakrishna Institute of Technology (Autonomous)' },
  { code:'2726', name:'S N S College of Technology (Autonomous), Coimbatore' },
  { code:'2727', name:'Sri Shakthi Institute of Engineering and Technology (Autonomous)' },
  { code:'2729', name:'Nehru Institute of Engineering and Technology, Coimbatore' },
  { code:'2731', name:'R V S College of Engineering and Technology, Coimbatore' },
  { code:'2732', name:'INFO Institute of Engineering, Coimbatore' },
  { code:'2733', name:'Angel College of Engineering and Technology, Coimbatore' },
  { code:'2734', name:'S N S College of Engineering (Autonomous), Coimbatore' },
  { code:'2735', name:'Karpagam Institute of Technology, Coimbatore' },
  { code:'2736', name:'Dr. N G P Institute of Technology, Coimbatore' },
  { code:'2737', name:'Sri Sai Ranganathan Engineering College, Coimbatore' },
  { code:'2739', name:'Sri Eshwar College of Engineering (Autonomous), Coimbatore' },
  { code:'2740', name:'Hindustan Institute of Technology (Autonomous), Coimbatore' },
  { code:'2741', name:'P A College of Engineering and Technology (Autonomous), Palladam' },
  { code:'2743', name:'Dhanalakshmi Srinivasan College of Engineering, Coimbatore' },
  { code:'2744', name:'Adithya Institute of Technology, Coimbatore' },
  { code:'2745', name:'Kathir College of Engineering, Coimbatore' },
  { code:'2747', name:'Shree Venkateshwara Hi-Tech Engineering College' },
  { code:'2748', name:'Surya Engineering College, Erode' },
  { code:'2749', name:'EASA College of Engineering and Technology, Coimbatore' },
  { code:'2750', name:'KIT-Kalaignar Karunanidhi Institute of Technology (Autonomous), Coimbatore' },
  { code:'2751', name:'KGISL Institute of Technology, Coimbatore' },
  { code:'2752', name:'Nandha College of Technology, Erode' },
  { code:'2753', name:'P P G Institute of Technology, Coimbatore' },
  { code:'2755', name:'Nehru Institute of Technology, Coimbatore' },
  { code:'2758', name:'J K K Muniraja College of Technology, Erode' },
  { code:'2761', name:'United Institute of Technology, Coimbatore' },
  { code:'2762', name:'Jansons Institute of Technology, Coimbatore' },
  { code:'2763', name:'Akshaya College of Engineering and Technology, Coimbatore' },
  { code:'2764', name:'K P R Institute of Engineering and Technology (Autonomous), Coimbatore' },
  { code:'2767', name:'SRG Engineering College, Namakkal' },
  { code:'2768', name:'Park College of Technology, Coimbatore' },
  { code:'2769', name:'J C T College of Engineering and Technology, Coimbatore' },
  { code:'2770', name:'Study World College of Engineering, Coimbatore' },
  { code:'2772', name:'C M S College of Engineering and Technology, Coimbatore' },
  { code:'2776', name:'R V S Technical Campus, Coimbatore' },
  { code:'3410', name:'Krishnaswamy College of Engineering and Technology' },
  { code:'3425', name:'C K College of Engineering and Technology, Cuddalore' },
  { code:'3451', name:'SMR East Coast College of Engineering and Technology' },
  { code:'3454', name:'Sri Ramakrishna College of Engineering, Tiruchirappalli' },
  { code:'3456', name:'K S K College of Engineering and Technology, Thanjavur' },
  { code:'3460', name:'Surya College of Engineering, Tiruchirappalli' },
  { code:'3461', name:'Arifa Institute of Technology, Tiruchirappalli' },
  { code:'3462', name:'Ariyalur Engineering College' },
  { code:'3466', name:'Nelliandavar Institute of Technology' },
  { code:'3701', name:'K Ramakrishnan College of Technology (Autonomous), Trichy' },
  { code:'3760', name:'Sir Issac Newton College of Engineering and Technology' },
  { code:'3766', name:'Star Lion College of Engineering and Technology' },
  { code:'3782', name:'OASYS Institute of Technology, Musiri' },
  { code:'3786', name:'M.A.M. School of Engineering, Tiruchirappalli' },
  { code:'3795', name:'SRM TRP Engineering College, Tiruchirappalli' },
  { code:'3801', name:'A V C College of Engineering, Mayiladuthurai' },
  { code:'3802', name:'Shri Angalamman College of Engineering and Technology' },
  { code:'3803', name:'Anjalai Ammal-Mahalingam Engineering College, Thanjavur' },
  { code:'3804', name:'Arasu Engineering College, Kumbakonam' },
  { code:'3805', name:'Dhanalakshmi Srinivasan Engineering College (Autonomous)' },
  { code:'3806', name:'E G S Pillay Engineering College (Autonomous), Nagapattinam' },
  { code:'3807', name:'J J College of Engineering and Technology, Trichy' },
  { code:'3808', name:'Jayaram College of Engineering and Technology, Trichy' },
  { code:'3809', name:'Kurinji College of Engineering and Technology, Manapparai' },
  { code:'3810', name:'M.A.M. College of Engineering, Tiruchirappalli' },
  { code:'3811', name:'M I E T Engineering College, Tiruchirappalli' },
  { code:'3812', name:'Mookambigai College of Engineering, Pudukkottai' },
  { code:'3813', name:'Oxford Engineering College, Tiruchirappalli' },
  { code:'3814', name:'P R Engineering College, Thanjavur' },
  { code:'3815', name:'Pavendhar Bharathidasan College of Engineering and Technology' },
  { code:'3817', name:'Roever Engineering College, Perambalur' },
  { code:'3819', name:'Saranathan College of Engineering, Tiruchirappalli' },
  { code:'3820', name:'Trichy Engineering College, Tiruchirappalli' },
  { code:'3821', name:'A R J College of Engineering and Technology, Mannargudi' },
  { code:'3822', name:'Dr. Navalar Nedunchezhian College of Engineering' },
  { code:'3825', name:'St. Josephs College of Engineering and Technology, Salem' },
  { code:'3826', name:'Kongunadu College of Engineering and Technology (Autonomous)' },
  { code:'3829', name:'M.A.M. College of Engineering and Technology, Trichy' },
  { code:'3830', name:'K Ramakrishnan College of Engineering (Autonomous), Trichy' },
  { code:'3831', name:'Indra Ganesan College of Engineering, Trichy' },
  { code:'3833', name:'Parisutham Institute of Technology and Science, Thanjavur' },
  { code:'3841', name:'CARE College of Engineering, Tiruchirappalli' },
  { code:'3843', name:'M R K Institute of Technology, Trichy' },
  { code:'3844', name:'Shivani Engineering College, Tiruchirappalli' },
  { code:'3846', name:'Mother Terasa College of Engineering and Technology' },
  { code:'3848', name:'Vandayar Engineering College, Thanjavur' },
  { code:'3849', name:'Annai College of Engineering and Technology, Thanjavur' },
  { code:'3850', name:'Vetri Vinayaha College of Engineering and Technology, Namakkal' },
  { code:'3852', name:'Sri Bharathi Engineering College for Women' },
  { code:'3854', name:'Mahath Amma Institute of Engineering and Technology (MIET)' },
  { code:'3855', name:'As-Salam College of Engineering and Technology, Thanjavur' },
  { code:'3857', name:'Meenakshi Ramaswamy Engineering College, Trichy' },
  { code:'3859', name:'Sembodai Rukmani Varatharajan Engineering College' },
  { code:'3860', name:'St. Annes College of Engineering and Technology' },
  { code:'3905', name:'Kings College of Engineering, Pudukkottai' },
  { code:'3908', name:'Mount Zion College of Engineering and Technology, Pudukkottai' },
  { code:'3918', name:'Shanmuganathan Engineering College, Pudukkottai' },
  { code:'3920', name:'Sudharsan Engineering College, Pudukkottai' },
  { code:'3926', name:'Chenduran College of Engineering and Technology' },
  { code:'4669', name:'Thamirabharani Engineering College, Tirunelveli' },
  { code:'4670', name:'Rohini College of Engineering and Technology, Kanyakumari' },
  { code:'4672', name:'Stella Marys College of Engineering, Kanyakumari' },
  { code:'4675', name:'Universal College of Engineering and Technology, Kanyakumari' },
  { code:'4676', name:'Renganayagi Varatharaj College of Engineering, Sivakasi' },
  { code:'4677', name:'Lourdes Mount College of Engineering and Technology' },
  { code:'4678', name:'Ramco Institute of Technology, Virudhunagar' },
  { code:'4680', name:'AAA College of Engineering and Technology, Virudhunagar' },
  { code:'4686', name:'Good Shepherd College of Engineering and Technology' },
  { code:'4864', name:'V V College of Engineering, Kanyakumari' },
  { code:'4917', name:'Sethu Institute of Technology (Autonomous), Virudhunagar' },
  { code:'4927', name:'Maria College of Engineering and Technology' },
  { code:'4928', name:'MAR Ephraem College of Engineering and Technology' },
  { code:'4929', name:'M E T Engineering College, Kanyakumari' },
  { code:'4931', name:'Grace College of Engineering, Kanyakumari' },
  { code:'4932', name:'Immanuel Arasar J J College of Engineering, Kanyakumari' },
  { code:'4933', name:'St. Mother Theresa Engineering College, Thoothukudi' },
  { code:'4934', name:'Holy Cross Engineering College, Thoothukudi' },
  { code:'4937', name:'A R College of Engineering and Technology' },
  { code:'4938', name:'Sivaji College of Engineering and Technology' },
  { code:'4941', name:'Unnamalai Institute of Technology, Kovilpatti' },
  { code:'4943', name:'Satyam College of Engineering and Technology' },
  { code:'4944', name:'Arunachala College of Engineering for Women, Nagercoil' },
  { code:'4945', name:'Vins Christian Womens College of Engineering, Nagercoil' },
  { code:'4946', name:'D M I Engineering College, Kanyakumari' },
  { code:'4948', name:'Rajas Institute of Technology, Nagercoil' },
  { code:'4949', name:'P S N Institute of Technology and Science, Tirunelveli' },
  { code:'4952', name:'C S I Institute of Technology, Kanyakumari' },
  { code:'4953', name:'CAPE Institute of Technology, Tirunelveli' },
  { code:'4954', name:'Dr. Sivanthi Aditanar College of Engineering, Tiruchendur' },
  { code:'4955', name:'Francis Xavier Engineering College (Autonomous), Tirunelveli' },
  { code:'4956', name:'Jayamatha Engineering College, Kanyakumari' },
  { code:'4957', name:'Jayaraj Annapackiam CSI College of Engineering, Tirunelveli' },
  { code:'4959', name:'Kamaraj College of Engineering and Technology (Autonomous)' },
  { code:'4960', name:'Mepco Schlenk Engineering College (Autonomous), Sivakasi' },
  { code:'4961', name:'Nellai College of Engineering, Tirunelveli' },
  { code:'4962', name:'National Engineering College (Autonomous), Kovilpatti' },
  { code:'4964', name:'P S N College of Engineering and Technology (Autonomous)' },
  { code:'4965', name:'P S R Engineering College (Autonomous), Tirunelveli' },
  { code:'4966', name:'PET Engineering College, Tirunelveli' },
  { code:'4967', name:'S Veerasamy Chettiar College of Engineering and Technology' },
  { code:'4968', name:'Sardar Raja College of Engineering, Tenkasi' },
  { code:'4969', name:'SCAD College of Engineering and Technology, Tirunelveli' },
  { code:'4970', name:'Sree Sowdambiga College of Engineering, Virudhunagar' },
  { code:'4971', name:'St. Xavier Catholic College of Engineering, Nagercoil' },
  { code:'4972', name:'AMRITA College of Engineering and Technology, Kanyakumari' },
  { code:'4975', name:'Dr. G U Pope College of Engineering, Thoothukudi' },
  { code:'4976', name:'Infant Jesus College of Engineering, Thoothukudi' },
  { code:'4977', name:'Narayanaguru College of Engineering, Kanyakumari' },
  { code:'4978', name:'Udaya School of Engineering, Kanyakumari' },
  { code:'4980', name:'Einstein College of Engineering, Tirunelveli' },
  { code:'4981', name:'Ponjesly College of Engineering, Nagercoil' },
  { code:'4982', name:'Vins Christian College of Engineering, Nagercoil' },
  { code:'4983', name:'Lord Jegannath College of Engineering and Technology' },
  { code:'4984', name:'Marthandam College of Engineering and Technology' },
  { code:'4989', name:'P S N Engineering College, Tirunelveli' },
  { code:'4992', name:'Bethlahem Institute of Engineering, Kanyakumari' },
  { code:'4993', name:'Loyola Institute of Technology and Science, Tenkasi' },
  { code:'4994', name:'J P College of Engineering, Tenkasi' },
  { code:'4995', name:'P.S.R.R College of Engineering, Tirunelveli' },
  { code:'4996', name:'Sri Vidhya College of Engineering and Technology, Sivakasi' },
  { code:'4998', name:'Mahakavi Bharathiyar College of Engineering and Technology' },
  { code:'4999', name:'Annai Vailankanni College of Engineering, Kanyakumari' },
  { code:'5502', name:'Sree Raaja Raajan College of Engineering and Technology' },
  { code:'5530', name:'SSM Institute of Engineering and Technology, Dindigul' },
  { code:'5532', name:'Vaigai College of Engineering, Madurai' },
  { code:'5533', name:'Karaikudi Institute of Technology' },
  { code:'5536', name:'Mangayarkarasi College of Engineering, Madurai' },
  { code:'5537', name:'Jainee College of Engineering and Technology, Dindigul' },
  { code:'5703', name:'Christian College of Engineering and Technology, Dindigul' },
  { code:'5720', name:'Sri Subramanya College of Engineering and Technology' },
  { code:'5832', name:'N P R College of Engineering and Technology, Dindigul' },
  { code:'5842', name:'Madurai Institute of Engineering and Technology' },
  { code:'5862', name:'R V S Educational Trusts Groups of Institutions, Dindigul' },
  { code:'5865', name:'Nadar Saraswathi College of Engineering and Technology' },
  { code:'5902', name:'Bharath Niketan Engineering College, Madurai' },
  { code:'5904', name:'K L N College of Engineering (Autonomous), Madurai' },
  { code:'5907', name:'Mohamed Sathak Engineering College, Ramanathapuram' },
  { code:'5910', name:'P S N A College of Engineering and Technology, Dindigul' },
  { code:'5911', name:'P T R College of Engineering and Technology, Madurai' },
  { code:'5912', name:'Pandian Saraswathi Yadav Engineering College, Madurai' },
  { code:'5913', name:'R V S College of Engineering, Dindigul' },
  { code:'5914', name:'Solamalai College of Engineering, Madurai' },
  { code:'5915', name:'SACS-M A V M M Engineering College, Madurai' },
  { code:'5919', name:'St. Michael College of Engineering and Technology, Sivaganga' },
  { code:'5921', name:'Syed Ammal Engineering College, Ramanathapuram' },
  { code:'5924', name:'Ganapathy Chettiar College of Engineering and Technology' },
  { code:'5930', name:'SBM College of Engineering and Technology, Dindigul' },
  { code:'5935', name:'Fatima Michael College of Engineering and Technology' },
  { code:'5942', name:'Ultra College of Engineering and Technology, Madurai' },
  { code:'5986', name:'Velammal College of Engineering and Technology, Madurai' },
  { code:'5988', name:'Theni Kammavar Sangam College of Technology, Theni' },
  { code:'5990', name:'Latha Mathavan Engineering College, Madurai' },
  { code:'2684', name:'Tips School of Architecture, Coimbatore' },
];
let BRANCHES = [];

let _dataLoaded = false;
let _dataLoadingPromise = null;

async function loadCollegesAndBranches() {
    if (_dataLoaded) return;
    if (_dataLoadingPromise) return _dataLoadingPromise;

    _dataLoadingPromise = (async () => {
        try {
            const [colRes, brRes] = await Promise.all([
                fetch(`${API_BASE}/predict/colleges-list`),
                fetch(`${API_BASE}/predict/branches-list`)
            ]);

            if (!colRes.ok || !brRes.ok) throw new Error('API not ready');

            const colData = await colRes.json();
            const brData  = await brRes.json();

            if (!Array.isArray(colData) || !Array.isArray(brData)) throw new Error('Invalid data');

            COLLEGES = colData.map(c => ({
                code: String(c.college_code).padStart(4, '0'),
                name: c.college_name_full,
                type: c.college_type,
                district: c.district
            }));
            BRANCHES = brData.map(b => ({
                code: b.branch_code,
                name: b.branch_name
            }));
            _dataLoaded = true;
            console.log(`Loaded ${COLLEGES.length} colleges and ${BRANCHES.length} branches from API`);
        } catch(e) {
            console.warn('API data load failed, using fallback data:', e.message);
            // fallback: COLLEGES already has hardcoded data from const declaration
            // rebuild BRANCHES from DATA.courses if available
            if (typeof DATA !== 'undefined' && DATA.courses) {
                BRANCHES = DATA.courses.map(c => ({
                    code: c.code || c.name.substring(0,2).toUpperCase(),
                    name: c.name
                }));
            }
            _dataLoaded = true;
        }
    })();

    return _dataLoadingPromise;
}

// ============================================================
// COURSES DATA
// ============================================================
const DATA = {
  courses: [
    { id:'cse',   name:'Computer Science & Engineering',   dept:'CS', cutoffBase:195 },
    { id:'aids',  name:'AI & Data Science',                dept:'CS', cutoffBase:192 },
    { id:'csbs',  name:'CS & Business Systems',            dept:'CS', cutoffBase:190 },
    { id:'it',    name:'Information Technology',           dept:'IT', cutoffBase:188 },
    { id:'ece',   name:'Electronics & Communication Eng.', dept:'EC', cutoffBase:185 },
    { id:'eee',   name:'Electrical & Electronics Eng.',    dept:'EE', cutoffBase:175 },
    { id:'bio',   name:'Biotechnology',                    dept:'BT', cutoffBase:172 },
    { id:'mech',  name:'Mechanical Engineering',           dept:'ME', cutoffBase:170 },
    { id:'chem',  name:'Chemical Engineering',             dept:'CH', cutoffBase:165 },
    { id:'civil', name:'Civil Engineering',                dept:'CV', cutoffBase:160 },
  ],

  testimonials: [
    { name:'Priya R.',   sub:'CSE · Anna University · 2024', text:'Got exactly the college PickMySeat predicted! Saved so many hours of confusion during counselling.', stars:5 },
    { name:'Karthik S.', sub:'ECE · PSG Tech · 2024',        text:'The AI Choice List helped me order my preferences perfectly. Made 3x smarter decisions.',            stars:5 },
    { name:'Ananya M.',  sub:'IT · SRM IST · 2024',          text:'Even without my rank, the marks-based prediction was spot on. Worth every rupee.',                    stars:5 },
    { name:'Vijay K.',   sub:'Mech · Thiagarajar · 2024',    text:'Used the counselling simulation to practice. When real day came, I was fully confident.',             stars:5 },
    { name:'Deepika T.', sub:'EEE · CEG · 2024',             text:'Loved how simple it was. Just entered marks, got my prediction in seconds. Brilliant!',               stars:5 },
    { name:'Ravi N.',    sub:'Civil · Kongu Engg · 2024',    text:'The probability ordering is genius. Knew exactly which college to put first in my list.',            stars:4 },
  ],

  tickerEvents: [
    'Priya from Chennai just predicted her seat 🎯',
    'Karthik unlocked Premium access ⚡',
    'Ananya got 94% probability for CSE at Anna Univ 🏛️',
    'Vijay ran the Counselling Simulation 🎓',
    'Deepika from Coimbatore got her AI Choice List 📋',
    'Ravi predicted rank band: 1200–1800 🏆',
    'Sneha unlocked 15 college-course combos 🚀',
    '3 students joined PickMySeat in the last hour 🔥',
  ],
};

// ============================================================
// THEME — Light / Dark toggle
// ============================================================
function togglePasswordVisibility(inputId, btn) {
  const input = document.getElementById(inputId);
  if (!input) return;
  if (input.type === 'password') {
    input.type = 'text';
    btn.textContent = '🙈';
  } else {
    input.type = 'password';
    btn.textContent = '👁️';
  }
}

function initTheme() {
  const saved = localStorage.getItem('pms_theme') || 'light';
  setTheme(saved);
}

function setTheme(theme) {
  App.theme = theme;
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('pms_theme', theme);
  const btn = document.getElementById('themeToggle');
  if (btn) btn.textContent = theme === 'dark' ? '☀️' : '🌙';
}

function toggleTheme() {
  setTheme(App.theme === 'dark' ? 'light' : 'dark');
}

// ============================================================
// SEARCHABLE COLLEGE DROPDOWN
// Renders a custom searchable dropdown for college selection
// ============================================================
async function buildCollegeSearchDropdown(containerId, onSelect, placeholder = 'Search by name or code...') {
  if (COLLEGES.length === 0) await loadCollegesAndBranches();
  const container = document.getElementById(containerId);
  if (!container) return;

  let filtered = [...COLLEGES];
  let selectedCollege = null;

  container.innerHTML = `
    <div class="college-search-wrap" id="csw_${containerId}">
      <div class="college-search-input-row">
        <input
          type="text"
          class="text-input college-search-input"
          id="csi_${containerId}"
          placeholder="${placeholder}"
          autocomplete="off"
        />
        <button class="college-clear-btn hidden" id="ccb_${containerId}" onclick="clearCollegeSearch('${containerId}')">✕</button>
      </div>
      <div class="college-dropdown-list hidden" id="cdl_${containerId}"></div>
      <div class="college-selected hidden" id="csel_${containerId}"></div>
    </div>`;

  const input    = document.getElementById(`csi_${containerId}`);
  const list     = document.getElementById(`cdl_${containerId}`);
  const clearBtn = document.getElementById(`ccb_${containerId}`);
  const selEl    = document.getElementById(`csel_${containerId}`);

  function renderList(colleges) {
    if (!colleges.length) {
      list.innerHTML = `<div class="college-no-result">No colleges found. Try a different search.</div>`;
} else {
      list.innerHTML = colleges.map(c => `
        <div class="college-option" onclick="selectCollegeOption('${containerId}', '${c.code}')">
          <span class="college-code-tag">${c.code}</span>
          <span class="college-option-name">${c.name}</span>
        </div>`).join('');
      list.innerHTML += `<div class="college-more-note">${colleges.length} colleges · scroll or type to search</div>`;
    }
    list.classList.remove('hidden');
  }

  input.addEventListener('focus', () => {
    filtered = [...COLLEGES];
    renderList(filtered);
  });

  input.addEventListener('input', () => {
    const q = input.value.toLowerCase().trim();
    clearBtn.classList.toggle('hidden', !q);
    filtered = COLLEGES.filter(c =>
      c.name.toLowerCase().includes(q) || c.code.includes(q)
    );
    renderList(filtered);
  });

  document.addEventListener('click', e => {
    if (!container.contains(e.target)) {
      list.classList.add('hidden');
    }
  });

  // Store callback
  container._onSelect = onSelect;
}

function selectCollegeOption(containerId, code) {
  const college  = COLLEGES.find(c => c.code === code);
  if (!college) return;

  const input    = document.getElementById(`csi_${containerId}`);
  const list     = document.getElementById(`cdl_${containerId}`);
  const selEl    = document.getElementById(`csel_${containerId}`);
  const clearBtn = document.getElementById(`ccb_${containerId}`);
  const container = document.getElementById(containerId);

  input.value = `[${college.code}] ${college.name}`;
  list.classList.add('hidden');
  clearBtn.classList.remove('hidden');

  selEl.innerHTML = `
    <div class="college-selected-chip">
      <span class="college-code-tag">${college.code}</span>
      <span>${college.name}</span>
    </div>`;
  selEl.classList.remove('hidden');

  if (container._onSelect) container._onSelect(college);
}

function clearCollegeSearch(containerId) {
  const input    = document.getElementById(`csi_${containerId}`);
  const list     = document.getElementById(`cdl_${containerId}`);
  const selEl    = document.getElementById(`csel_${containerId}`);
  const clearBtn = document.getElementById(`ccb_${containerId}`);
  const container = document.getElementById(containerId);

  input.value = '';
  list.classList.add('hidden');
  selEl.classList.add('hidden');
  clearBtn.classList.add('hidden');

  if (container._onSelect) container._onSelect(null);
}

// ============================================================
// ROUTING
// ============================================================
async function navigateTo(page) {
  document.querySelectorAll('.page').forEach(p => {
    p.classList.remove('active');
    p.classList.add('hidden');
  });
  const target = document.getElementById(`page-${page}`);
  if (target) {
    target.classList.remove('hidden');
    target.classList.add('active');
  }
  App.currentPage = page;
  window.scrollTo({ top:0, behavior:'smooth' });
  updateNav();
  if (page === 'dashboard')    renderDashboard();
  if (page === 'profile')    { await loadCollegesAndBranches(); renderProfile(); }
  if (page === 'free-predict') initFreePredictPage();
  if (page === 'landing')      initLanding();
}

// ============================================================
// NAV
// ============================================================
function updateNav() {
  const navUser    = document.getElementById('navUserBlock');
  const navLogin   = document.getElementById('navLoginBtn');
  const navUpgrade = document.getElementById('navUpgradeBtn');
  const navDash    = document.getElementById('navDashboard');
  const navProf    = document.getElementById('navProfile');
  const themeBtn   = document.getElementById('themeToggle');

  if (App.currentUser) {
    navUser.classList.remove('hidden');
    navLogin.classList.add('hidden');
    navDash.classList.remove('hidden');
    navProf.classList.remove('hidden');
    document.getElementById('navAvatar').textContent =
      (App.profile.name || App.profile.email || 'S')[0].toUpperCase();
    document.getElementById('navUserName').textContent =
      App.profile.name ? App.profile.name.split(' ')[0] : 'Student';
    document.getElementById('dropdownInfo').textContent = App.profile.email || '';
    navUpgrade.classList.toggle('hidden', App.userGrade === 1);
    if (themeBtn) themeBtn.style.display = 'flex';
  } else {
    navUser.classList.add('hidden');
    navLogin.classList.remove('hidden');
    navUpgrade.classList.add('hidden');
    navDash.classList.add('hidden');
    navProf.classList.add('hidden');
    if (themeBtn) themeBtn.style.display = 'none';
    setTheme('light');
  }
}

function toggleUserMenu() {
  document.getElementById('userDropdown')?.classList.toggle('hidden');
}

document.addEventListener('click', e => {
  const dd = document.getElementById('userDropdown');
  if (dd && !dd.classList.contains('hidden') && !e.target.closest('.nav-user')) {
    dd.classList.add('hidden');
  }
});

// ============================================================
// TOAST
// ============================================================
let toastTimeout = null;
function showToast(msg, type = 'info', duration) {
  const toast = document.getElementById('toast');
  if (!toast) return;
  if (duration == null) duration = 5000;        // success/info auto-dismiss after 5s
  if (toastTimeout) clearTimeout(toastTimeout); // cancel any prior toast's timer
  toast.textContent = msg;
  toast.className = `toast show ${type}`;   // no 'hidden' => visible (.toast.hidden is the hide rule)
  toastTimeout = setTimeout(() => {
    console.log('[showToast] auto-dismiss fired after', duration, 'ms');
    toast.classList.remove('show');
    toast.classList.add('hidden');          // .toast.hidden { display:none } actually hides it
  }, duration);
}

// ============================================================
// LOADER
// ============================================================
function showLoader() {
  document.body.classList.add('loading');
}

function hideLoader() {
  document.body.classList.remove('loading');
}

// ============================================================
// ERROR HANDLING
// ============================================================
let errorTimeout = null;

function showError(message, statusCode = null) {
  clearError();
  let msg = message;

  if (statusCode === 429) {
    msg = 'Too many predictions today. Come back tomorrow for more free predictions, or login to continue.';
  }

  if (statusCode === 401) {
    msg = 'Session expired. Please log in again.';
    localStorage.removeItem('token');
    App.currentUser = null;
    App.userGrade = 3;
    errorTimeout = setTimeout(() => {
      updateNav();
      navigateTo('landing');
    }, 2000);
  } else if (statusCode === 422) {
    msg = 'Please check your inputs and try again.';
  } else if (statusCode === 500) {
    msg = 'Server error. Please try again in a moment.';
  }

  const toast = document.getElementById('error-toast');
  if (toast) {
    toast.textContent = msg;
    toast.classList.add('visible');
    if (!errorTimeout) {
      errorTimeout = setTimeout(() => {
        toast.classList.remove('visible');
        errorTimeout = null;
      }, 4000);
    }
  }
}

function clearError() {
  if (errorTimeout) {
    clearTimeout(errorTimeout);
    errorTimeout = null;
  }
  const toast = document.getElementById('error-toast');
  if (toast) toast.classList.remove('visible');
}

// ============================================================
// LANDING
// ============================================================
function initLanding() {
  renderTicker();
  renderTestimonials();
  updateLiveCounts();
  observeScrollAnimations();
}

function renderTicker() {
  const track = document.getElementById('tickerTrack');
  if (!track) return;
  const doubled = [...DATA.tickerEvents, ...DATA.tickerEvents];
  track.innerHTML = doubled.map(ev => `<span class="ticker-item">🟢 ${ev}</span>`).join('');
}

function renderTestimonials() {
  const grid = document.getElementById('testimonialsGrid');
  if (!grid) return;
  grid.innerHTML = DATA.testimonials.map(t => `
    <div class="testimonial-card animate-on-scroll">
      <div class="testimonial-stars">${'★'.repeat(t.stars)}${'☆'.repeat(5 - t.stars)}</div>
      <p class="testimonial-text">"${t.text}"</p>
      <div class="testimonial-author">
        <div class="testimonial-avatar">${t.name[0]}</div>
        <div>
          <div class="testimonial-name">${t.name}</div>
          <div class="testimonial-sub">${t.sub}</div>
        </div>
      </div>
    </div>`).join('');
}

function updateLiveCounts() {
  const heroCount  = document.getElementById('heroLiveCount');
  const modalCount = document.getElementById('liveCount');
  const update = () => {
    if (heroCount)  heroCount.textContent  = App.liveCount;
    if (modalCount) modalCount.textContent = App.liveCount;
    localStorage.setItem('pms_live_count', App.liveCount);
  };
  update();
  setInterval(() => {
    if (Math.random() > 0.7) { App.liveCount++; update(); }
  }, 8000);
}

function incrementPredictionCount() {
  App.liveCount++;
  const heroCount  = document.getElementById('heroLiveCount');
  const modalCount = document.getElementById('liveCount');
  if (heroCount)  heroCount.textContent  = App.liveCount;
  if (modalCount) modalCount.textContent = App.liveCount;
  localStorage.setItem('pms_live_count', App.liveCount);
}

function observeScrollAnimations() {
  const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.style.animation = 'slideUp 0.5s ease forwards';
        observer.unobserve(entry.target);
      }
    });
  }, { threshold:0.1 });
  document.querySelectorAll('.animate-on-scroll').forEach(el => {
    el.style.opacity = '0';
    observer.observe(el);
  });
}

// ============================================================
// AGGREGATE FORMULA
// (M/2) + (P/4) + (C/4) → max 100 → ×2 = max 200
// ============================================================
function calculateAggregate(maths, physics, chemistry) {
  const m = Math.min(100, Math.max(0, parseFloat(maths)     || 0));
  const p = Math.min(100, Math.max(0, parseFloat(physics)   || 0));
  const c = Math.min(100, Math.max(0, parseFloat(chemistry) || 0));
  return Math.round(((m / 2) + (p / 4) + (c / 4)) * 2 * 100) / 100;
}

// ============================================================
// PREDICTION ENGINE
// Simulates XGBoost — replace with POST /predict/rank
// cutoffBase is college-agnostic; college tier adjusts it
// For 550 colleges: government top tier -0, aided -5, private -15
// Individual college prestige further adjusts (+/- 10)
// ============================================================
function predictRankBand(aggregate) {
  const r = parseFloat(aggregate) / 200;
  if (r >= 0.975) return { low:1,     high:200   };
  if (r >= 0.95)  return { low:200,   high:600   };
  if (r >= 0.925) return { low:600,   high:1500  };
  if (r >= 0.90)  return { low:1500,  high:3000  };
  if (r >= 0.875) return { low:3000,  high:5500  };
  if (r >= 0.85)  return { low:5500,  high:9000  };
  if (r >= 0.825) return { low:9000,  high:14000 };
  if (r >= 0.80)  return { low:14000, high:20000 };
  if (r >= 0.75)  return { low:20000, high:30000 };
  if (r >= 0.70)  return { low:30000, high:45000 };
  return                  { low:45000, high:80000 };
}

function getProbClass(prob) {
  if (prob >= 65) return { cls:'high', barCls:'high', status:'Likely',   statusCls:'status-likely'   };
  if (prob >= 35) return { cls:'mid',  barCls:'mid',  status:'Possible', statusCls:'status-possible' };
  return           { cls:'low',  barCls:'low',  status:'Unlikely', statusCls:'status-unlikely' };
}

// ============================================================
// FREE PREDICT — Grade 3
// ============================================================
let freeSelectedCollege = null;

function initFreePredictPage() {
  const used = getCookie('pms_free_used');
  const bar  = document.getElementById('cookieUsageBar');

  freeSelectedCollege = null;

  if (used === '1') {
    bar.textContent = '🔒 Free prediction used · Login to predict more';
    bar.style.display = 'inline-block';
    document.getElementById('freePredictForm')
      ?.querySelectorAll('input,select').forEach(el => el.disabled = true);
    const btn = document.querySelector('#freePredictForm .btn-primary.predict-btn');
    if (btn) btn.disabled = true;
  } else {
    bar.textContent = '✅ 1 free prediction available — no signup needed';
    bar.style.display = 'inline-block';
  }

  // Build searchable college dropdown for free predict
buildCollegeSearchDropdown('freeCollegeSearchContainer', async (college) => {
    freeSelectedCollege = college;
    if (college) {
        const branches = await getBranchesForColleges([college.code]);
        populateCourseDropdown('freeCourse', branches.length ? branches : BRANCHES);
    } else {
        populateCourseDropdown('freeCourse', BRANCHES);
    }
}, 'Search college by name or code...');

  populateAllCourses('freeCourse');
  document.getElementById('freeResultCard').classList.add('hidden');
}

function populateCourseDropdown(selectId, branches) {
    const sel = document.getElementById(selectId);
    if (!sel) return;
    const current = sel.value;
    sel.innerHTML = '<option value="">Select a course...</option>';
    branches.forEach(b => {
        const opt = document.createElement('option');
        opt.value = b.name;
        opt.textContent = b.name;
        sel.appendChild(opt);
    });
    if (current) sel.value = current;
}

// Per-college branch cache — official branch codes from the backend
const _collegeBranchCache = {};

async function getBranchesForColleges(collegeCodes) {
    if (!collegeCodes || collegeCodes.length === 0) return [];
    try {
        const results = await Promise.all(
            collegeCodes.map(async code => {
                const key = String(parseInt(code));
                if (_collegeBranchCache[key]) {
                    console.log("branches for college", key, "(cached):", _collegeBranchCache[key].map(b => b.code));
                    return _collegeBranchCache[key];
                }
                const r = await fetch(`${API_BASE}/predict/colleges/${parseInt(code)}/branches`);
                if (!r.ok) return [];
                const data = await r.json();
                const mapped = Array.isArray(data)
                    ? data.map(b => ({ code: b.branch_code, name: b.branch_name }))
                    : [];
                _collegeBranchCache[key] = mapped;
                console.log("branches for college", key, "(fetched):", mapped.map(b => b.code));
                return mapped;
            })
        );
        // union of ALL selected colleges' branches, deduplicated by branch code
        const seen = new Set();
        const merged = [];
        results.flat().forEach(b => {
            if (!seen.has(b.code)) {
                seen.add(b.code);
                merged.push(b);
            }
        });
        console.log("final branch union:", merged.map(b => b.code));
        return merged;
    } catch(e) {
        return [];
    }
}

function updateFreeAggregate() {
  const m   = document.getElementById('freeMath')?.value     || 0;
  const p   = document.getElementById('freePhysics')?.value  || 0;
  const c   = document.getElementById('freeChemistry')?.value|| 0;
  const agg = calculateAggregate(m, p, c);
  const el  = document.getElementById('freeAggValue');
  if (el) el.textContent = agg > 0 ? `${agg} / 200` : '— / 200';
  updateBar('mathBar',    m, 100);
  updateBar('physicsBar', p, 100);
  updateBar('chemBar',    c, 100);
}

function updateBar(id, value, max) {
  const bar = document.getElementById(id);
  if (bar) bar.style.width = `${Math.min(100,(parseFloat(value)/max)*100)}%`;
}

async function runFreePrediction() {
  if (getCookie('pms_free_used') === '1') {
    showToast('Free prediction already used. Please login to continue.', 'error'); return;
  }
  const m      = document.getElementById('freeMath')?.value      || '';
  const p      = document.getElementById('freePhysics')?.value   || '';
  const c      = document.getElementById('freeChemistry')?.value || '';
  const course = document.getElementById('freeCourse')?.value;

  if (!m || !p || !c) {
    showToast('Please enter all three marks', 'error'); return;
  }
  if (parseFloat(m)>100 || parseFloat(p)>100 || parseFloat(c)>100) {
    showToast('Each mark must be between 0 and 100', 'error'); return;
  }
  if (parseFloat(m)<0 || parseFloat(p)<0 || parseFloat(c)<0) {
    showToast('Marks cannot be negative', 'error'); return;
  }
  const btn = document.querySelector('#freePredictForm .predict-btn');
  if (btn) { btn.disabled = true; btn.textContent = 'Predicting...'; }

  const agg = calculateAggregate(m, p, c);

  const branchObj  = BRANCHES.find(b => b.name === course || b.code === course);
  const branchCode = branchObj ? branchObj.code : course;

  let prob = 0, rankBand = { low: 0, high: 0 }, cutoff = '—', ok = false, recs = [];

  try {
    showLoader();
    // plain fetch — Grade 3 is a guest (no token); authenticatedFetch would fail silently
    const res = await fetch(`${API_BASE}/predict/colleges`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        maths:              parseFloat(m),
        physics:            parseFloat(p),
        chemistry:          parseFloat(c),
        community:          document.getElementById('freeCategory')?.value || 'OC',
        top_n:              freeSelectedCollege ? 1 : 5,
        preferred_colleges: freeSelectedCollege ? [parseInt(freeSelectedCollege.code)] : null,
        preferred_branches: (branchCode && branchCode !== '') ? [branchCode] : null
      })
    });
    if (res.status === 429) {
      showError('Too many predictions today. Come back tomorrow.', 429);
      return;
    }
    const data = await res.json();
    console.log('[freePredict] status:', res.status, 'body:', data);
    if (!res.ok) throw new Error(data.detail || `HTTP ${res.status}`);
    recs       = data.recommendations || [];
    const rec  = recs[0];
    prob       = rec ? rec.match_confidence : 0;
    rankBand   = { low: data.student_rank_range?.[0], high: data.student_rank_range?.[1] };
    cutoff     = rec ? rec.closing_rank : '—';
    ok = true;
  } catch(e) {
    console.error('[freePredict] failed:', e);
    showError('Something went wrong. Please try again.');
  } finally {
    hideLoader();
    if (btn) { btn.disabled = false; btn.textContent = 'Predict My Seat'; }
  }

  if (!ok) return;   // failed — leave form usable so the guest can retry

  if (freeSelectedCollege) {
    renderFreeResult({
      agg, prob, rankBand, cutoff,
      college: `[${freeSelectedCollege.code}] ${freeSelectedCollege.name}`,
      course: course || 'All branches'
    });
  } else {
    renderFreeResultList({ agg, rankBand, recs, course: course || 'All branches' });
  }

  setCookie('pms_free_used', '1', 7);
  incrementPredictionCount();

  document.getElementById('freePredictForm')
    ?.querySelectorAll('input,select').forEach(el => el.disabled = true);
  if (btn) btn.disabled = true;
  const bar = document.getElementById('cookieUsageBar');
  if (bar) bar.textContent = '🔒 Free prediction used · Login to predict more';
}

function renderFreeResult({ agg, prob, rankBand, cutoff, college, course }) {
  document.getElementById('resultCollegeName').textContent = college;
  document.getElementById('resultCourseName').textContent  = course;
  document.getElementById('resultAggregate').textContent   = `${agg} / 200`;
  document.getElementById('resultCutoff').textContent      = cutoff !== '—' ? `Rank ${cutoff}` : '—';
  document.getElementById('resultRankBand').textContent    =
    rankBand.low ? `${rankBand.low.toLocaleString()} – ${rankBand.high.toLocaleString()}` : '—';

  const pc   = getProbClass(prob);
  const ring = document.getElementById('probRingCircle');
  ring.style.stroke = prob>=65 ? 'var(--success)' : prob>=35 ? 'var(--warning)' : 'var(--danger)';
  ring.style.strokeDashoffset = 314 - (314 * prob / 100);

  document.getElementById('resultProbPercent').textContent = `${prob}%`;
  document.getElementById('resultStatus').textContent      = pc.status;
  document.getElementById('resultStatus').style.color      =
    prob>=65 ? 'var(--success)' : prob>=35 ? 'var(--warning)' : 'var(--danger)';

  const msgEl = document.getElementById('resultMessage');
  if (prob >= 65) {
    msgEl.textContent = `🎉 Strong chance! Your aggregate of ${agg} is above the typical cutoff for this college-course combo.`;
    msgEl.className   = 'result-message success';
  } else if (prob >= 35) {
    msgEl.textContent = `⚡ Possible. You're in the competitive zone. Rank ${rankBand.low?.toLocaleString()}–${rankBand.high?.toLocaleString()} may get you in.`;
    msgEl.className   = 'result-message warning';
  } else {
    msgEl.textContent = `⚠️ Very competitive. Your aggregate of ${agg} is below the typical cutoff of ${cutoff}. Consider safer options.`;
    msgEl.className   = 'result-message danger';
  }

  document.querySelector('.probability-display')?.classList.remove('hidden');
  document.getElementById('freeResultList')?.classList.add('hidden');

  document.getElementById('freeResultCard').classList.remove('hidden');
  document.getElementById('freeResultCard').scrollIntoView({ behavior:'smooth', block:'start' });
}

function renderFreeResultList({ agg, rankBand, recs, course }) {
  document.getElementById('resultCollegeName').textContent = 'Top colleges for your marks';
  document.getElementById('resultCourseName').textContent  = course;

  // single-result probability ring not applicable for a list
  document.querySelector('.probability-display')?.classList.add('hidden');

  const list = document.getElementById('freeResultList');
  if (list) {
    if (!recs.length) {
      list.innerHTML = `<div class="free-result-empty">No colleges matched your marks. Try adjusting your inputs.</div>`;
    } else {
      list.innerHTML = recs.map(r => {
        const pc = getProbClass(r.match_confidence);
        return `
          <div class="free-result-row">
            <div class="free-result-row-main">
              <div class="free-result-college">
                <span class="college-code-tag small">${r.college_code}</span>${r.college_name}
              </div>
              <div class="free-result-branch">${r.branch_name}</div>
              <div class="free-result-meta">Closing Rank: ${r.closing_rank} · Agg: ${agg}/200</div>
            </div>
            <div class="free-result-row-prob">
              <div class="free-result-pct" style="color:${r.match_confidence>=65?'var(--success)':r.match_confidence>=35?'var(--warning)':'var(--danger)'}">${r.match_confidence}%</div>
              <span class="combo-status-tag ${pc.statusCls}">${pc.status}</span>
            </div>
          </div>`;
      }).join('');
    }
    list.classList.remove('hidden');
  }

  const msgEl = document.getElementById('resultMessage');
  if (msgEl) {
    const band = rankBand.low ? `${rankBand.low.toLocaleString()} – ${rankBand.high.toLocaleString()}` : '—';
    msgEl.textContent = `Your aggregate ${agg}/200 · Predicted rank band ${band}. Showing your best ${recs.length} matches.`;
    msgEl.className   = 'result-message';
  }

  document.getElementById('freeResultCard').classList.remove('hidden');
  document.getElementById('freeResultCard').scrollIntoView({ behavior:'smooth', block:'start' });
}

// ============================================================
// AUTH
// ============================================================
function switchAuth(mode) {
  document.getElementById('loginForm') ?.classList.toggle('hidden', mode !== 'login');
  document.getElementById('signupForm')?.classList.toggle('hidden', mode !== 'signup');
  document.getElementById('loginTab')  ?.classList.toggle('active', mode === 'login');
  document.getElementById('signupTab') ?.classList.toggle('active', mode === 'signup');
}

async function loginUser() {
  const email    = document.getElementById('loginEmail')?.value?.trim();
  const password = document.getElementById('loginPassword')?.value;
  if (!email || !password) { showToast('Please enter email and password', 'error'); return; }
  showLoader();
  try {
    const res  = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    const data = await res.json();
    if (!res.ok) { showError(data.detail || 'Login failed', res.status); return; }
    localStorage.setItem('token', data.token);
    await restoreSessionFromToken();   // load stored marks/community into App.profile
    simulateLogin({ email, name: data.name, hasPaid: data.grade === '1' });
    prefillAndLockMarks();
  } catch(e) {
    showError('No connection. Check your internet and retry.');
  } finally {
    hideLoader();
  }
}

async function signupUser() {
  const name     = document.getElementById('signupName')?.value?.trim();
  const email    = document.getElementById('signupEmail')?.value?.trim();
  const mobile   = document.getElementById('signupMobile')?.value?.trim();
  const password = document.getElementById('signupPassword')?.value;
  const category = document.getElementById('signupCategory')?.value || 'OC';
  const termsAccepted = document.getElementById('signupTermsCheckbox')?.checked;
  if (!termsAccepted) {
    showError('Please accept the Terms of Service and Privacy Policy to continue.');
    return;
  }
  if (!name || !email || !mobile || !password) {
    showToast('Please fill all fields', 'error'); return;
  }
  if (password.length < 8) {
    showToast('Password must be at least 8 characters', 'error'); return;
  }
  showLoader();
  try {
    const res  = await fetch(`${API_BASE}/auth/signup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, name, mobile, community: category })
    });
    const data = await res.json();
    if (!res.ok) { showError(data.detail || 'Signup failed', res.status); return; }
    localStorage.setItem('token', data.token);
    simulateLogin({ email, name: data.name, mobile, hasPaid: false });
  } catch(e) {
    showError('No connection. Check your internet and retry.');
  } finally {
    hideLoader();
  }
}

function simulateLogin(userData) {
  App.currentUser     = userData;
  App.profile.email   = userData.email  || '';
  App.profile.name    = userData.name   || '';
  App.profile.mobile  = userData.mobile || App.profile.mobile || '';
  App.profile.hasPaid = userData.hasPaid || false;
  App.userGrade       = userData.hasPaid ? 1 : 2;
  showToast(`Welcome${userData.name ? ', ' + userData.name.split(' ')[0] : ''}! 🎉`, 'success');
  navigateTo('profile');
}

function logout() {
  localStorage.removeItem('token');
  setTheme('light');
  App.currentUser = null;
  App.userGrade   = 3;
  App.profile     = {
    name:'', email:'', mobile:'', category:'',
    maths:null, physics:null, chemistry:null,
    marksLocked:false, rank:null, rankPhase:'pre',
    hasPaid:false, preferredColleges:[], preferredCourses:[],
  };
  showToast('Logged out', 'info');
  navigateTo('landing');
}

// ============================================================
// PROFILE
// ============================================================
function renderProfile() {
  if (!App.currentUser) { navigateTo('auth'); return; }

  document.getElementById('profileName').value     = App.profile.name          || '';
  document.getElementById('profileEmail').value    = App.profile.email         || '';
  document.getElementById('profileMobile').value   = App.profile.mobile        || '';
  const appIdBasicEl = document.getElementById('profileApplicationId');
  if (appIdBasicEl) appIdBasicEl.value = App.profile.applicationId || '';
  document.getElementById('profileCategory').value = App.profile.category || '';

  const locked = App.profile.marksLocked;
  // exactly one lock banner: Grade 1 gets "Update for ₹25", others "contact support"
  document.getElementById('marksLockedBanner')
    ?.classList.toggle('hidden', !(locked && App.userGrade === 1));

  ['profileMath','profilePhysics','profileChemistry'].forEach(id => {
    const el  = document.getElementById(id);
    const key = id.replace('profile','').toLowerCase();
    if (el) {
      el.value    = App.profile[key] ?? '';
      el.disabled = locked;
      el.classList.toggle('locked', locked);
    }
  });
  if (document.getElementById('profileMath'))
    document.getElementById('profileMath').value = App.profile.maths ?? '';
  if (document.getElementById('profilePhysics'))
    document.getElementById('profilePhysics').value = App.profile.physics ?? '';
  if (document.getElementById('profileChemistry'))
    document.getElementById('profileChemistry').value = App.profile.chemistry ?? '';

  const marksLockNote = document.getElementById('marksLockNote');
  if (marksLockNote) {
    if (locked && App.userGrade !== 1) {
      marksLockNote.classList.remove('hidden');
      marksLockNote.textContent = '🔒 Marks locked — contact support to update';
    } else {
      marksLockNote.classList.add('hidden');
    }
  }

  updateProfileAggregate();

  document.getElementById('profileRankSection')
    ?.classList.toggle('hidden', App.userGrade !== 1);

    if (App.rankListReleased) {
  const appIdSection = document.getElementById('profileAppIdSection');
  if (appIdSection) {
    appIdSection.classList.remove('hidden');
    const appIdInput = document.getElementById('profileAppId');
    if (appIdInput) appIdInput.value = App.profile.applicationId || '';
  }
}

  if (App.userGrade === 1 && App.profile.rank) {
    const rankEl = document.getElementById('profileRank');
    if (rankEl) rankEl.value = App.profile.rank;
  }

  renderPreferredColleges();
  renderPreferredCourses();
}

function updateProfileAggregate() {
  const m   = document.getElementById('profileMath')?.value     || 0;
  const p   = document.getElementById('profilePhysics')?.value  || 0;
  const c   = document.getElementById('profileChemistry')?.value|| 0;
  const agg = calculateAggregate(m, p, c);
  const el  = document.getElementById('profileAggValue');
  if (el) el.textContent = agg > 0 ? `${agg} / 200` : '— / 200';
}

function markProfileDirty() {}

// Pre-fill marks/community inputs from App.profile, then lock them if
// App.profile.marksLocked. Null-safe: no-ops when inputs aren't on the page.
function prefillAndLockMarks() {
  const fields = {
    profileMath:     'maths',
    profilePhysics:  'physics',
    profileChemistry:'chemistry',
    profileCategory: 'category',
  };
  Object.entries(fields).forEach(([id, key]) => {
    const el  = document.getElementById(id);
    const val = App.profile[key];
    if (el && val != null && val !== '') el.value = val;
  });

  const locked = App.profile.marksLocked === true;
  Object.keys(fields).forEach(id => {
    const el = document.getElementById(id);
    if (el) {
      el.disabled = locked;
      el.classList.toggle('locked', locked);
    }
  });

  // exactly one lock banner: Grade 1 gets "Update for ₹25", others "contact support"
  document.getElementById('marksLockedBanner')
    ?.classList.toggle('hidden', !(locked && App.userGrade === 1));
  const note = document.getElementById('marksLockNote');
  if (note) {
    note.classList.toggle('hidden', !(locked && App.userGrade !== 1));
    if (locked) note.textContent = '🔒 Marks locked — contact support to update';
  }
}

function setRankPhase(phase) {
  App.rankPhase = phase;
  App.profile.rankPhase = phase;
  const label = document.getElementById('rankInputLabel');
  const input = document.getElementById('profileRank');
  if (phase === 'post') {
    if (label) label.textContent = 'Your Actual TNEA Rank (will be verified)';
    if (input) input.setAttribute('placeholder','e.g. 4521');
  } else {
    if (label) label.textContent = 'Predicted Rank (optional)';
    if (input) input.setAttribute('placeholder','e.g. 5000');
  }
}

// ============================================================
// PREFERRED COLLEGES — Grade 2: max 5, Grade 1: unlimited search
// ============================================================
async function renderPreferredColleges() {
  if (COLLEGES.length === 0) await loadCollegesAndBranches();
  const grid = document.getElementById('preferredCollegesGrid');
  if (!grid) return;
  grid.innerHTML = '';

  const isPremium = App.userGrade === 1;
  const max       = isPremium ? Infinity : 5;
  const current   = App.profile.preferredColleges;

  // Show added colleges
  current.forEach((college, i) => {
    grid.innerHTML += `
      <div class="preferred-slot filled">
        <div class="slot-number">${i+1}</div>
        <div class="slot-content">
          <div class="slot-name">
            <span class="college-code-tag small">${college.code}</span>
            ${college.name}
          </div>
        </div>
        <button class="slot-remove" onclick="removePreferredCollege(${i})">✕</button>
      </div>`;
  });

  // Add slot — Grade 2: max 5, Grade 1: always show add
  const canAdd = isPremium ? true : current.length < 5;
  if (canAdd) {
    const addId = `addCollegeSearch_${Date.now()}`;
    grid.innerHTML += `
      <div class="preferred-slot add-slot" style="flex-direction:column;align-items:stretch;gap:8px;height:auto;padding:12px">
        <div style="font-size:12px;color:var(--text-muted);margin-bottom:4px">
          ${isPremium ? '+ Add any college (Premium — unlimited)' : `+ Add College ${current.length+1} of 5`}
        </div>
        <div id="${addId}"></div>
      </div>`;

    // Init search after render
    setTimeout(() => {
      buildCollegeSearchDropdown(addId, (college) => {
        if (college) addPreferredCollege(college);
      }, 'Search by name or code...');
    }, 0);
  }

  if (!isPremium && current.length >= 5) {
    grid.innerHTML += `
      <div style="grid-column:1/-1;font-size:13px;color:var(--text-muted);padding:8px 0">
        Maximum 5 colleges for Student plan.
        <button class="link-btn" onclick="showUpgradeModal('colleges')">
          Upgrade to Premium for unlimited →
        </button>
      </div>`;
  }
}

async function renderPreferredCourses() {
  if (BRANCHES.length === 0) await loadCollegesAndBranches();
  const collegeCodes = App.profile.preferredColleges.map(c => c.code);
  const availableBranches = await getBranchesForColleges(collegeCodes);
  const grid = document.getElementById('preferredCoursesGrid');
  if (!grid) return;
  grid.innerHTML = '';
  const max = 3;

  for (let i = 0; i < max; i++) {
    const course = App.profile.preferredCourses[i];
    if (course) {
      grid.innerHTML += `
        <div class="preferred-slot filled">
          <div class="slot-number">${i+1}</div>
          <div class="slot-content">
            <div class="slot-name">${course.name}</div>
            <div class="slot-sub">${course.code || course.dept || ''}</div>
          </div>
          <button class="slot-remove" onclick="removePreferredCourse(${i})">✕</button>
        </div>`;
    } else if (i === App.profile.preferredCourses.length) {
      grid.innerHTML += `
        <div class="preferred-slot add-slot">
          <select class="select-input" onchange="addPreferredCourse(this.value);this.value=''">
            <option value="">+ Add Course ${i+1}</option>
            ${availableBranches.length
              ? availableBranches.map(b=>`<option value="${b.code}">${b.name}</option>`).join('')
              : `<option value="" disabled>Select colleges first to see available courses</option>`}
          </select>
        </div>`;
    } else {
      grid.innerHTML += `
        <div class="preferred-slot" style="opacity:0.25;pointer-events:none">
          <div class="slot-number">${i+1}</div>
          <div class="slot-content"><div class="slot-name">Add Course ${i+1}</div></div>
        </div>`;
    }
  }
}

function addPreferredCollege(college) {
  if (!college) return;
  if (App.profile.preferredColleges.find(c => c.code === college.code)) {
    showToast('College already added','error'); renderPreferredColleges(); return;
  }
  if (App.userGrade !== 1 && App.profile.preferredColleges.length >= 5) {
    showToast('Maximum 5 colleges for Student plan','error'); return;
  }
  App.profile.preferredColleges.push(college);
  renderPreferredColleges();
  renderPreferredCourses();   // rebuild course dropdown with the new union
  showToast(`[${college.code}] ${college.name} added ✅`, 'success');
}

function removePreferredCollege(i) {
  App.profile.preferredColleges.splice(i,1);
  renderPreferredColleges();
  renderPreferredCourses();   // rebuild course dropdown with the new union
}

function addPreferredCourse(code) {
  if (!code) return;
  // resolve from the per-college cache first so the official code + name
  // from the backend is what gets stored; BRANCHES as backup
  let course = null;
  for (const list of Object.values(_collegeBranchCache)) {
    course = list.find(c => c.code === code);
    if (course) break;
  }
  if (!course) course = BRANCHES.find(c => c.code === code);
  if (!course) return;
  if (App.profile.preferredCourses.find(c => c.code === code)) {
    showToast('Course already added','error'); renderPreferredCourses(); return;
  }
  if (App.profile.preferredCourses.length >= 3) {
    showToast('Maximum 3 courses','error'); return;
  }
  App.profile.preferredCourses.push(course);
  renderPreferredCourses();
}

function removePreferredCourse(i) {
  App.profile.preferredCourses.splice(i,1);
  renderPreferredCourses();
}

async function saveProfile() {
  const name  = document.getElementById('profileName')?.value?.trim();
  const email = document.getElementById('profileEmail')?.value?.trim();

  if (!name)  { showToast('Please enter your name','error');  return; }
  if (!email) { showToast('Please enter your email','error'); return; }

  App.profile.name     = name;
  App.profile.email    = email;
  App.profile.mobile   = document.getElementById('profileMobile')?.value?.trim()    || '';
  App.profile.applicationId = document.getElementById('profileApplicationId')?.value?.trim() || App.profile.applicationId || '';
  App.profile.category = document.getElementById('profileCategory')?.value          || '';

  const marksWereLocked = App.profile.marksLocked;
  if (!App.profile.marksLocked) {
    const m = parseFloat(document.getElementById('profileMath')?.value)     || null;
    const p = parseFloat(document.getElementById('profilePhysics')?.value)  || null;
    const c = parseFloat(document.getElementById('profileChemistry')?.value)|| null;

    if (m !== null || p !== null || c !== null) {
      if (!m || !p || !c) {
        showToast('Please enter all three marks or leave all blank','error'); return;
      }
      if (m > 100 || p > 100 || c > 100) {
        showToast('Each mark must be between 0 and 100','error'); return;
      }
      if (m < 0 || p < 0 || c < 0) {
        showToast('Marks cannot be negative', 'error'); return;
      }
      App.profile.maths     = m;
      App.profile.physics   = p;
      App.profile.chemistry = c;
      App.profile.marksLocked = true;
    }
  }

  if (App.userGrade === 1) {
    const rank = parseFloat(document.getElementById('profileRank')?.value) || null;
    if (rank) {
      App.profile.rank      = rank;
      App.profile.rankPhase = App.rankPhase;
      if (App.rankPhase === 'post') {
        const agg  = calculateAggregate(App.profile.maths, App.profile.physics, App.profile.chemistry);
        const band = predictRankBand(agg);
        const verEl= document.getElementById('rankVerifyResult');
        if (verEl) {
          verEl.classList.remove('hidden');
          const within = rank >= band.low && rank <= band.high;
          verEl.style.cssText = within
            ? 'background:rgba(16,185,129,0.1);border:1px solid rgba(16,185,129,0.2);color:var(--success);padding:12px;border-radius:8px;font-size:13px;margin-top:8px'
            : 'background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.2);color:var(--danger);padding:12px;border-radius:8px;font-size:13px;margin-top:8px';
          verEl.textContent = within
            ? `✅ Rank ${rank.toLocaleString()} verified — within predicted band`
            : `⚠️ Rank ${rank.toLocaleString()} outside predicted band (${band.low.toLocaleString()}–${band.high.toLocaleString()}). Model updating.`;
        }
      }
    }
  }

if (App.currentUser) {
    showLoader();
    try {
      const body = {
        name: App.profile.name,
        mobile: App.profile.mobile,
        community: App.profile.category,
        preferred_colleges: JSON.stringify(App.profile.preferredColleges),
        preferred_courses: JSON.stringify(App.profile.preferredCourses)
      };
      // Marks are locked server-side after first save — sending them again gets a 403
      // that discards the whole update, including preferences.
      if (!marksWereLocked) {
        body.maths     = App.profile.maths;
        body.physics   = App.profile.physics;
        body.chemistry = App.profile.chemistry;
      }
      const res = await authenticatedFetch(`${API_BASE}/auth/update-profile`, {
        method: 'POST',
        body: JSON.stringify(body)
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        showToast(err.detail || 'Could not save profile to server', 'error');
        hideLoader();
        return;
      }
    } catch(e) {
      showToast('No connection — profile saved locally only', 'error');
    } finally {
      hideLoader();
    }
  }
  showToast('Profile saved ✅', 'success');
  setTimeout(() => navigateTo('dashboard'), 800);
}

// ============================================================
// MARKS UPDATE — ₹25 (Grade 1 only)
// ============================================================
function openMarksUpdate() {
  if (App.userGrade !== 1) { showUpgradeModal('marks-update'); return; }
  const mEl = document.getElementById('updateMath');
  const pEl = document.getElementById('updatePhysics');
  const cEl = document.getElementById('updateChemistry');
  if (mEl) mEl.value = App.profile.maths    || '';
  if (pEl) pEl.value = App.profile.physics  || '';
  if (cEl) cEl.value = App.profile.chemistry|| '';
  document.getElementById('marksUpdateModal')?.classList.remove('hidden');
}

function closeMarksUpdate() {
  document.getElementById('marksUpdateModal')?.classList.add('hidden');
}

async function confirmMarksUpdate() {
  const m = parseFloat(document.getElementById('updateMath')?.value)     || null;
  const p = parseFloat(document.getElementById('updatePhysics')?.value)  || null;
  const c = parseFloat(document.getElementById('updateChemistry')?.value)|| null;
  if (!m || !p || !c) { showToast('Please enter all three marks','error'); return; }
  if (m>100 || p>100 || c>100) { showToast('Each mark must be 0–100','error'); return; }

  const btn = document.querySelector('#marksUpdateModal .btn-primary');
  if (btn) { btn.disabled = true; btn.textContent = 'Processing...'; }

  showLoader();
  try {
    const res = await authenticatedFetch(`${API_BASE}/payment/create-order-marks`, {
      method: 'POST'
    });
    const data = await res.json();
    if (!res.ok) { showError(data.detail || 'Could not start payment'); return; }

    const rzp = new Razorpay({
      key:         data.key_id,
      amount:      data.amount,
      currency:    data.currency,
      order_id:    data.order_id,
      name:        'PickMySeat',
      description: 'Marks Update — ₹25',
      prefill: {
        name:  data.user_name  || '',
        email: data.user_email || ''
      },
      theme: { color: '#6C63FF' },
      handler: async function(response) {
        const verRes = await authenticatedFetch(`${API_BASE}/payment/verify-marks`, {
          method: 'POST',
          body: JSON.stringify({
            razorpay_payment_id: response.razorpay_payment_id,
            razorpay_order_id:   response.razorpay_order_id,
            razorpay_signature:  response.razorpay_signature,
            maths: m, physics: p, chemistry: c
          })
        });
        const verData = await verRes.json();
        if (!verRes.ok) { showError('Payment verified but marks update failed. Contact support.'); return; }
        App.profile.maths     = m;
        App.profile.physics   = p;
        App.profile.chemistry = c;
        App.profile.marksLocked = true;
        closeMarksUpdate();
        showToast('Marks updated successfully ✅', 'success');
        renderDashboard();
      },
      modal: {
        ondismiss: function() { showToast('Payment cancelled', 'error'); }
      }
    });
    rzp.open();
  } catch(e) {
    showError('No connection. Check your internet and retry.');
  } finally {
    hideLoader();
    if (btn) { btn.disabled = false; btn.textContent = 'Pay ₹25 & Update'; }
  }
}

// ============================================================
// DASHBOARD
// ============================================================
function renderDashboard() {
  if (!App.currentUser) { navigateTo('auth'); return; }

  const name = App.profile.name || App.profile.email || 'Student';
  document.getElementById('dashWelcome').textContent = `Welcome back, ${name.split(' ')[0]}`;

  const badge = document.getElementById('dashTierBadge');
  if (badge) {
    badge.textContent  = App.userGrade === 1 ? '⚡ Premium' : '🎓 Student';
    badge.style.cssText = App.userGrade === 1
      ? 'background:rgba(108,99,255,0.2);color:var(--accent);border:1px solid rgba(108,99,255,0.3);border-radius:100px;padding:6px 14px;font-size:12px;font-weight:700'
      : 'background:rgba(56,189,248,0.1);color:#38BDF8;border:1px solid rgba(56,189,248,0.2);border-radius:100px;padding:6px 14px;font-size:12px;font-weight:700';
  }

  renderDashProfileCard();
  renderAggBanner();
  renderGrade1RankInput();
  renderComboProbCards();
  renderLockedSections();
}

function renderDashProfileCard() {
  const card = document.getElementById('dashProfileCard');
  if (!card) return;
  const initials = App.profile.name
    ? App.profile.name.split(' ').map(w=>w[0]).join('').toUpperCase().slice(0,2)
    : (App.profile.email||'S')[0].toUpperCase();

  card.innerHTML = `
    <div class="dash-avatar">${initials}</div>
    <div class="dash-user-info">
      <div class="dash-user-name">${App.profile.name || 'Student'}</div>
      <div class="dash-user-meta">
        ${App.profile.email || ''}
        ${App.profile.mobile   ? ' · ' + App.profile.mobile   : ''}
        ${App.profile.category ? ' · ' + App.profile.category : ''}
      </div>
      <div class="dash-marks-chips">
        ${App.profile.maths     != null ? `<span class="mark-chip">Maths: ${App.profile.maths}</span>`     : ''}
        ${App.profile.physics   != null ? `<span class="mark-chip">Physics: ${App.profile.physics}</span>` : ''}
        ${App.profile.chemistry != null ? `<span class="mark-chip">Chem: ${App.profile.chemistry}</span>`  : ''}
        ${App.profile.maths == null
          ? `<span class="mark-chip" style="color:var(--warning)">⚠️ Add marks in Profile</span>` : ''}
        ${App.profile.marksLocked
          ? `<span class="mark-chip" style="color:var(--text-muted);border-color:rgba(245,158,11,0.3)">🔒 Marks locked</span>` : ''}
      </div>
    </div>`;
}

function renderAggBanner() {
  const banner = document.getElementById('dashAggBanner');
  if (!banner) return;
  const agg = calculateAggregate(
    App.profile.maths||0, App.profile.physics||0, App.profile.chemistry||0
  );
  const lockNote = App.profile.marksLocked
    ? `<div class="agg-lock-row">🔒 Marks locked ·
        ${App.userGrade === 1
          ? `<button class="link-btn" onclick="openMarksUpdate()">Update for ₹25 after board results</button>`
          : `<button class="link-btn" onclick="showUpgradeModal('marks-update')">Upgrade to Premium to update marks</button>`}
       </div>`
    : `<div style="font-size:13px;color:var(--text-muted);margin-top:6px">Marks will lock after first save</div>`;

  banner.innerHTML = `
    <div class="agg-main">
      <div class="agg-banner-label">Your TNEA Aggregate</div>
      <div class="agg-banner-value">${agg > 0 ? agg : '—'}</div>
      <div class="agg-banner-sub">Out of 200 · Maths + Physics + Chemistry</div>
      ${lockNote}
    </div>`;
}

function renderGrade1RankInput() {
  const section = document.getElementById('grade1RankInput');
  if (!section) return;
  const isGrade1 = App.profile && App.profile.grade === '1';
  section.classList.toggle('hidden', !isGrade1);
  if (isGrade1) {
    document.getElementById('submitRankInput').value = '';
  }
}

async function submitGrade1Rank() {
  const rankInput = document.getElementById('submitRankInput');
  if (!rankInput) return;
  const rank = rankInput.value.trim();
  if (!rank) return;

  showLoader();
  try {
    const res = await authenticatedFetch(`${API_BASE}/predict/submit-rank`, {
      method: 'POST',
      body: JSON.stringify({ rank: parseInt(rank) })
    });
    const data = await res.json();
    if (!res.ok) { showError(data.detail || 'Failed to save rank', res.status); return; }
    rankInput.value = '';
    showToast('Rank saved. Thank you!', 'success');
  } catch(e) {
    showError('No connection. Check your internet and retry.');
  } finally {
    hideLoader();
  }
}

async function renderComboProbCards() {
  const grid = document.getElementById('comboProbGrid');
  if (!grid) return;
  const colleges = App.profile.preferredColleges;
  const courses  = App.profile.preferredCourses;

  if (!colleges.length || !courses.length) {
    grid.innerHTML = `
      <div style="grid-column:1/-1;text-align:center;padding:48px;color:var(--text-muted)">
        <div style="font-size:40px;margin-bottom:16px">🏛️</div>
        <p style="font-size:17px;font-weight:700;margin-bottom:8px;color:var(--text-dim)">No Preferences Added Yet</p>
        <p style="font-size:14px;margin-bottom:24px">
          Add your preferred colleges and courses in your profile to see probability predictions
        </p>
        <button class="btn-primary" onclick="navigateTo('profile')">Add Preferences →</button>
      </div>`;
    return;
  }

  // fetch once; per-combo evaluation happens below, OUTSIDE the try block —
  // an exception mid-loop used to jump to catch and stamp EVERY pair noData
  // on top of combos already pushed, so one failure bled into all cards
  let recs = [], rankLow = 0, rankHigh = 0;

  showLoader();
  try {
    const collegeCodes  = colleges.map(c => parseInt(c.code));
    const branchCodes   = courses.map(c => c.code);
    const res = await authenticatedFetch(`${API_BASE}/predict/colleges`, {
      method: 'POST',
      body: JSON.stringify({
        maths: App.profile.maths || 0,
        physics: App.profile.physics || 0,
        chemistry: App.profile.chemistry || 0,
        community: App.profile.category || 'OC',
        top_n: 50,
        preferred_colleges: collegeCodes,
        preferred_branches: branchCodes
      })
    });
    if (res.status === 429) {
      showError('Too many predictions today. Come back tomorrow.', 429);
      return;
    }
    const data = await res.json();
    console.log('API response:', JSON.stringify(data, null, 2));
    if (!res.ok) {
      console.error('predict/colleges failed:', res.status, data);
    } else {
      recs     = data.recommendations || [];
      rankLow  = data.student_rank_range?.[0] || 0;
      rankHigh = data.student_rank_range?.[1] || 0;
      incrementPredictionCount();
    }
  } catch(e) {
    console.error('predict/colleges request error:', e);
  } finally {
    hideLoader();
  }
  console.log("RAW RECS:", JSON.stringify(recs, null, 2));

  // each (college, course) pair evaluated independently — one combo's state
  // can never affect another
  const combos = [];
  colleges.forEach(college => {
    courses.forEach(course => {
      let combo;
      try {
        const match = recs.find(r =>
          r.college_code === parseInt(college.code) &&
          r.branch_code === course.code
        );
        console.log("COMBO:", college.code, course.code,
        "match:", JSON.stringify(match));
        if (match && match.not_offered) {
          combo = { college, course, notOffered: true };
        } else if (!match || match.match_confidence == null) {
          combo = { college, course, noData: true };
        } else {
          combo = {
            college, course,
            prob: match.match_confidence,
            closingRank: match.closing_rank,
            estimated: !!match.no_community_data,
            rankLow, rankHigh
          };
        }
      } catch(e) {
        console.error('combo evaluation failed for', college.code, course.code, e);
        combo = { college, course, noData: true };
      }
      combos.push(combo);
    });
  });

  combos.sort((a,b) => (b.prob ?? -1) - (a.prob ?? -1));

  grid.innerHTML = combos.map(combo => {
    if (combo.notOffered || combo.noData) {
      return `
        <div class="combo-card prob-low" style="opacity:0.7">
          <div style="display:flex;align-items:center;gap:6px;margin-bottom:2px">
            <span class="college-code-tag small">${combo.college.code}</span>
            <div class="combo-college">${combo.college.name}</div>
          </div>
          <div class="combo-course">${combo.course.name}</div>
          <div class="combo-prob-label" style="margin-top:12px">
            ${combo.notOffered ? 'Course not offered by this college' : 'Data unavailable'}
          </div>
        </div>`;
    }
    const pc = getProbClass(combo.prob);
    return `
      <div class="combo-card prob-${pc.cls}">
        <div style="display:flex;align-items:center;gap:6px;margin-bottom:2px">
          <span class="college-code-tag small">${combo.college.code}</span>
          <div class="combo-college">${combo.college.name}</div>
        </div>
        <div class="combo-course">${combo.course.name}</div>
        <div class="combo-prob-bar-wrap">
          <div class="combo-prob-bar ${pc.barCls}" style="width:${combo.prob}%"></div>
        </div>
        <div class="combo-prob-row">
          <div>
            <div class="combo-prob-pct" style="color:${pc.cls==='high'?'var(--success)':pc.cls==='mid'?'var(--warning)':'var(--danger)'}">
              ${combo.prob}%
            </div>
           <div class="combo-prob-label">Closing Rank: ${combo.closingRank || '—'}</div>
           <div class="combo-prob-label" style="font-size:11px;color:var(--text-muted)">Rank Band: <span style="font-size:15px;font-weight:600;color:var(--text-secondary)">${combo.rankLow ? combo.rankLow.toLocaleString() + '–' + combo.rankHigh.toLocaleString() : '—'}</span></div>
           ${combo.estimated ? `<div class="combo-prob-label" style="font-size:11px;color:var(--text-muted)">⚠️ No historic data for your community — estimate based on overall cutoff</div>` : ''}
          </div>
          <span class="combo-status-tag ${pc.statusCls}">${pc.status}</span>
        </div>
      </div>`;
  }).join('');
}

// ============================================================
// PREMIUM SEARCH — on Dashboard for Grade 1
// Allows searching any college + any course for instant prediction
// ============================================================
function initPremiumSearch() {
  const wrap = document.getElementById('premiumSearchWrap');
  if (!wrap || App.userGrade !== 1) return;

  let premiumSelectedCollege = null;

  wrap.innerHTML = `
    <div class="dash-section-title" style="margin-top:40px">
      <h2>🔍 Quick Prediction — Any College</h2>
      <p>Premium: search any of the 550+ colleges instantly</p>
    </div>
    <div class="card" style="display:flex;flex-direction:column;gap:16px">
      <div id="premiumCollegeSearch"></div>
      <select class="select-input full-width" id="premiumCourseSelect">
        <option value="">Select a course...</option>
        ${(BRANCHES.length ? BRANCHES : DATA.courses).map(c=>`<option value="${c.name}">${c.name}</option>`).join('')}
      </select>
      <button class="btn-primary btn-glow" onclick="runPremiumQuickPredict()">
        🔮 Get Probability
      </button>
      <div id="premiumQuickResult" class="hidden"></div>
    </div>`;

  buildCollegeSearchDropdown('premiumCollegeSearch', (college) => {
    premiumSelectedCollege = college;
    wrap._selectedCollege = college;
  }, 'Search any college by name or code...');

  populateCourseDropdown('premiumCourseSelect', BRANCHES);
}

async function runPremiumQuickPredict() {
  const wrap   = document.getElementById('premiumSearchWrap');
  const course = document.getElementById('premiumCourseSelect')?.value;
  const college = wrap?._selectedCollege;

  if (!college) { showToast('Please select a college', 'error'); return; }
  if (!course)  { showToast('Please select a course', 'error'); return; }

  const agg = calculateAggregate(
    App.profile.maths||0, App.profile.physics||0, App.profile.chemistry||0
  );
  if (agg === 0) { showToast('Please add your marks in Profile first', 'error'); return; }

  const branchObj  = BRANCHES.find(b => b.name === course || b.code === course);
  const branchCode = branchObj ? branchObj.code : course;

  const btn = document.querySelector('#premiumSearchWrap .btn-primary');
  if (btn) { btn.disabled = true; btn.textContent = 'Predicting...'; }

  showLoader();
  try {
    const res = await authenticatedFetch(`${API_BASE}/predict/colleges`, {
      method: 'POST',
      body: JSON.stringify({
        maths:              App.profile.maths || 0,
        physics:            App.profile.physics || 0,
        chemistry:          App.profile.chemistry || 0,
        community:          App.profile.category || 'OC',
        top_n:              1,
        preferred_colleges: [parseInt(college.code)],
        preferred_branches: [branchCode]
      })
    });
    const data = await res.json();
    if (!res.ok) { showError(data.detail || 'Prediction failed', res.status); return; }

    const rec    = data.recommendations?.[0];
    if (rec && (rec.not_offered || rec.match_confidence == null)) {
      const result = document.getElementById('premiumQuickResult');
      if (result) {
        result.classList.remove('hidden');
        result.innerHTML = `
          <div style="padding:16px;background:var(--surface2);border-radius:var(--radius);border:1px solid var(--border2);color:var(--text-muted);font-size:14px">
            <span class="college-code-tag">${college.code}</span> ${college.name} · ${course}<br/>
            ${rec.not_offered ? 'Course not offered by this college' : 'Data unavailable'}
          </div>`;
      }
      return;
    }
    const prob   = rec ? rec.match_confidence : 0;
    const cutoff = rec ? rec.closing_rank : '—';
    const pc     = getProbClass(prob);

    const result = document.getElementById('premiumQuickResult');
    if (result) {
      result.classList.remove('hidden');
      result.innerHTML = `
        <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;padding:16px;background:var(--surface2);border-radius:var(--radius);border:1px solid var(--border2)">
          <div>
            <div style="font-size:12px;color:var(--text-muted);margin-bottom:2px">
              <span class="college-code-tag">${college.code}</span> ${college.name}
            </div>
            <div style="font-size:14px;font-weight:600;color:var(--text-dim)">${course}</div>
            <div style="font-size:12px;color:var(--text-muted);margin-top:4px">Closing Rank: ${cutoff} · Agg: ${agg}/200</div>
          </div>
          <div style="text-align:right">
            <div style="font-size:32px;font-weight:900;color:${prob>=65?'var(--success)':prob>=35?'var(--warning)':'var(--danger)'}">
              ${prob}%
            </div>
            <span class="combo-status-tag ${pc.statusCls}">${pc.status}</span>
          </div>
        </div>`;
    }
  } catch(e) {
    showError('No connection. Check your internet and retry.');
  } finally {
    hideLoader();
    if (btn) { btn.disabled = false; btn.textContent = '🔮 Get Probability'; }
  }
}

function renderLockedSections() {
  const isPremium = App.userGrade === 1;
  document.getElementById('rankLockOverlay')       ?.style.setProperty('display', isPremium?'none':'flex');
  document.getElementById('choiceLockOverlay')     ?.style.setProperty('display', isPremium?'none':'flex');
  document.getElementById('counsellingLockOverlay')?.style.setProperty('display', isPremium?'none':'flex');
  if (isPremium) {
    renderRankCard();
    renderChoiceList();
    renderCounsellingSimulation();
    setTimeout(initPremiumSearch, 100);
  }
}

async function renderRankCard() {
  const card = document.getElementById('dashRankCard');
  if (!card) return;
  const agg      = calculateAggregate(App.profile.maths||0, App.profile.physics||0, App.profile.chemistry||0);
let rankBand = { low: 0, high: 0 };
showLoader();
try {
  const res = await authenticatedFetch(`${API_BASE}/predict/rank`, {
    method: 'POST',
    body: JSON.stringify({
      maths: App.profile.maths || 0,
      physics: App.profile.physics || 0,
      chemistry: App.profile.chemistry || 0,
      community: App.profile.category || 'OC'
    })
  });
  if (res.status === 429) {
    showError('Too many predictions today. Come back tomorrow.', 429);
    return;
  }
  const data = await res.json();
  rankBand = { low: data.range_min, high: data.range_max };
} catch(e) {
  rankBand = predictRankBand(agg);
} finally {
  hideLoader();
}
  const phase    = App.profile.rankPhase || 'pre';
  let verifyHtml = '';
  if (phase === 'post' && App.profile.rank) {
    const within = App.profile.rank >= rankBand.low && App.profile.rank <= rankBand.high;
    verifyHtml = within
      ? `<div style="margin-top:12px;background:rgba(16,185,129,0.1);border:1px solid rgba(16,185,129,0.2);color:var(--success);padding:12px 16px;border-radius:8px;font-size:13px;font-weight:500">
           ✅ Rank #${App.profile.rank.toLocaleString()} verified — within predicted band
         </div>`
      : `<div style="margin-top:12px;background:rgba(239,68,68,0.1);border:1px solid rgba(239,68,68,0.2);color:var(--danger);padding:12px 16px;border-radius:8px;font-size:13px;font-weight:500">
           ⚠️ Rank #${App.profile.rank.toLocaleString()} is outside predicted band
           (${rankBand.low.toLocaleString()}–${rankBand.high.toLocaleString()}). Model updating.
         </div>`;
  }
  card.innerHTML = `
    <div style="display:flex;gap:32px;flex-wrap:wrap;align-items:flex-start">
      <div>
        <div style="font-size:13px;color:var(--text-muted);margin-bottom:6px">
          ${phase==='post' ? '🏆 Your Actual Rank' : '📊 Predicted Rank Band'}
        </div>
        <div style="font-size:36px;font-weight:900;color:var(--accent)">
          ${phase==='post' && App.profile.rank
            ? `#${App.profile.rank.toLocaleString()}`
            : agg > 0
              ? `${rankBand.low.toLocaleString()} – ${rankBand.high.toLocaleString()}`
              : 'Enter marks first'}
        </div>
        <div style="font-size:13px;color:var(--text-muted);margin-top:6px">
          Based on aggregate ${agg}/200 · TNEA 2024 model
        </div>
      </div>
      <div style="flex:1">
        ${verifyHtml}
        <div style="margin-top:12px;font-size:13px;color:var(--text-muted)">
          🔄 Probabilities update as more students submit marks
        </div>
      </div>
    </div>`;
}

async function renderChoiceList() {
  const wrap = document.getElementById('choiceListWrap');
  if (!wrap) return;
  const colleges = App.profile.preferredColleges;
  const courses  = App.profile.preferredCourses;

  if (!colleges.length || !courses.length) {
    wrap.innerHTML = `<div style="text-align:center;padding:40px;color:var(--text-muted)">
      Add preferred colleges and courses in your profile to generate the AI Choice List
    </div>`;
    return;
  }

  // fetch once; per-combo evaluation happens below, OUTSIDE the try block —
  // same isolation as renderComboProbCards
  let recs = [];

  showLoader();
  try {
    const collegeCodes = colleges.map(c => parseInt(c.code));
    const branchCodes  = courses.map(c => c.code);
    const res = await authenticatedFetch(`${API_BASE}/predict/colleges`, {
      method: 'POST',
      body: JSON.stringify({
        maths: App.profile.maths || 0,
        physics: App.profile.physics || 0,
        chemistry: App.profile.chemistry || 0,
        community: App.profile.category || 'OC',
        top_n: 50,
        preferred_colleges: collegeCodes,
        preferred_branches: branchCodes
      })
    });
    if (res.status === 429) {
      showError('Too many predictions today. Come back tomorrow.', 429);
      return;
    }
    const data = await res.json();
    if (!res.ok) {
      console.error('predict/colleges failed:', res.status, data);
    } else {
      recs = data.recommendations || [];
    }
  } catch(e) {
    console.error('predict/colleges request error:', e);
  } finally {
    hideLoader();
  }

  // each (college, course) pair evaluated independently
  const combos = [];
  colleges.forEach(college => {
    courses.forEach(course => {
      let combo;
      try {
        const match = recs.find(r =>
          r.college_code === parseInt(college.code) &&
          r.branch_code === course.code
        );
        if (match && match.not_offered) {
          combo = { college, course, notOffered: true };
        } else if (!match || match.match_confidence == null) {
          combo = { college, course, noData: true };
        } else {
          combo = { college, course, prob: match.match_confidence, closingRank: match.closing_rank };
        }
      } catch(e) {
        console.error('combo evaluation failed for', college.code, course.code, e);
        combo = { college, course, noData: true };
      }
      combos.push(combo);
    });
  });

  combos.sort((a,b) => (b.prob ?? -1) - (a.prob ?? -1));

  const viable   = combos.filter(c => c.prob != null && c.prob >= 35);
  const unlikely = combos.filter(c => c.prob != null && c.prob <  35);
  const excluded = combos.filter(c => c.prob == null);

  wrap.innerHTML = `
    <div style="font-size:12px;color:var(--text-muted);margin-bottom:16px;font-style:italic;padding:10px 14px;background:var(--surface2);border-radius:8px">
      🤖 AI-generated priority order based on your marks and TNEA 2021–2025 cutoff data.
      Submit your choices in this exact order for the best outcome.
    </div>
    ${viable.map((combo,idx) => {
      const pc = getProbClass(combo.prob);
      return `
        <div class="choice-item">
          <div class="choice-rank-num">${idx+1}</div>
          <div class="choice-info">
            <div class="choice-college">
              <span class="college-code-tag small">${combo.college.code}</span>
              ${combo.college.name}
            </div>
            <div class="choice-course">${combo.course.name}</div>
          </div>
          <div style="text-align:right">
            <div class="choice-prob" style="color:${combo.prob>=65?'var(--success)':'var(--warning)'}">
              ${combo.prob}%
            </div>
            <span class="combo-status-tag ${pc.statusCls}">${pc.status}</span>
          </div>
        </div>`;
    }).join('')}
    ${unlikely.length > 0 ? `
      <div class="choice-no-chance">
        ⚠️ ${unlikely.length} combination${unlikely.length>1?'s':''} below 35% probability —
        you are unlikely to be allotted these with your current marks:<br/>
        <span style="font-size:12px;margin-top:6px;display:block">
          ${unlikely.map(c=>`[${c.college.code}] ${c.college.name} · ${c.course.name} (${c.prob}%)`).join(' | ')}
        </span>
      </div>` : ''}
    ${excluded.length > 0 ? `
      <div class="choice-no-chance" style="margin-top:12px">
        ℹ️ ${excluded.length} combination${excluded.length>1?'s':''} excluded:<br/>
        <span style="font-size:12px;margin-top:6px;display:block">
          ${excluded.map(c=>`[${c.college.code}] ${c.college.name} · ${c.course.name} (${c.notOffered ? 'not offered by this college' : 'data unavailable'})`).join(' | ')}
        </span>
      </div>` : ''}`;
}

// ============================================================
// COUNSELLING SIMULATION — Full TNEA Flow
// ============================================================

const TFC_LIST = [
  'Government College of Technology, Coimbatore - 641013',
  'PSG College of Technology, Coimbatore - 641004',
  'CEG Campus, Anna University, Chennai - 600025',
  'Government College of Engineering, Salem - 636011',
  'Thiagarajar College of Engineering, Madurai - 625015',
  'Government College of Engineering, Tirunelveli - 627007',
  'Government College of Engineering, Bargur, Krishnagiri - 635104',
  'Alagappa Chettiar Govt College of Engineering, Karaikudi - 630003',
  'Government College of Engineering, Erode - 638316',
  'University College of Engineering, Villupuram - 605103',
];

const SIM_BRANCHES = [
  { code:'CS',   name:'COMPUTER SCIENCE AND ENGINEERING' },
  { code:'EC',   name:'ELECTRONICS AND COMMUNICATION ENGINEERING' },
  { code:'EE',   name:'ELECTRICAL AND ELECTRONICS ENGINEERING' },
  { code:'ME',   name:'MECHANICAL ENGINEERING' },
  { code:'CE',   name:'CIVIL ENGINEERING' },
  { code:'IT',   name:'INFORMATION TECHNOLOGY' },
  { code:'AIDS', name:'ARTIFICIAL INTELLIGENCE AND DATA SCIENCE' },
  { code:'CSBS', name:'COMPUTER SCIENCE AND BUSINESS SYSTEMS' },
  { code:'MECH', name:'MECHATRONICS ENGINEERING' },
  { code:'CHE',  name:'CHEMICAL ENGINEERING' },
];

function simCollegeType(code) {
  const govtCodes = ['0001','0002','0003','0004','0005','1516','2005','2369','2603','2615','2709','3464','3465','4974','5009','5901','1013','1014','1015','1026','3011','3016','3018','3019','3021','4020','4023','4024','5010','5017'];
  return govtCodes.includes(code) ? 'Govt' : parseInt(code) < 3000 ? 'Aided' : 'Self-Financing';
}

function simGetSeats(collegeCode, branchCode) {
  const h = (collegeCode + branchCode).split('').reduce((a,c)=>a+c.charCodeAt(0),0);
  const type = simCollegeType(collegeCode);
  const base = type==='Govt' ? 25 : type==='Aided' ? 45 : 60;
  return { oc: base + (h % 15), comm: Math.floor((base + (h%15)) * 0.3) + (h%7) };
}

function simGetCutoff(collegeCode, branchCode, community) {
  const h = (collegeCode+branchCode+community).split('').reduce((a,c)=>a+c.charCodeAt(0),0);
  const type = simCollegeType(collegeCode);
  const base = type==='Govt' ? 8000 : type==='Aided' ? 25000 : 80000;
  return base + (h % (type==='Govt' ? 15000 : 40000));
}

function simRunAllotment() {
  const rank = App.profile.rank || 99999;
  const community = App.profile.category || 'OC';
  for (const c of App.simChoices) {
    const cutoff = simGetCutoff(c.collegeCode, c.branchCode, community);
    if (rank <= cutoff) return { ...c, cutoff, community };
  }
  return null;
}

function simGoToStep(n) { App.simStep = n; renderCounsellingSimulation(); }

function simToggleChoice(collegeCode, branchCode, branchName, collegeName) {
  const idx = App.simChoices.findIndex(c=>c.collegeCode===collegeCode&&c.branchCode===branchCode);
  if (idx >= 0) {
    App.simChoices.splice(idx,1);
    App.simChoices.forEach((c,i)=>c.order=i+1);
  } else {
    App.simChoices.push({ collegeCode, branchCode, branchName, collegeName, order: App.simChoices.length+1 });
  }
  renderCounsellingSimulation();
}

function simClearChoices() { App.simChoices=[]; renderCounsellingSimulation(); }

function simLockAndAllot() {
  if (App.simChoices.length===0) { showToast('Add at least one choice first','error'); return; }
  App.simAllotment = simRunAllotment();
  simGoToStep(2);
}

function simConfirmAllotment() {
  const sel = document.querySelector('input[name="simOption"]:checked')?.value;
  if (!sel) { showToast('Please select an option','error'); return; }
  if (sel==='decline_quit') {
    showToast('You quit counselling in this simulation.','warning');
    resetCounselling(); return;
  }
  if (sel==='decline_next') {
    showToast('You moved to Round 2. Add more choices and try again.','warning');
    App.simChoices=[]; simGoToStep(1); return;
  }
  simGoToStep(3);
}

function renderCounsellingSimulation() {
  const sim = document.getElementById('counsellingSim');
  if (!sim) return;

  const stepLabels = ['📋 Status','✏️ Choice Filling','🏛️ Allotment','📄 Order'];
  const indicator = `<div class="sim-progress">
    ${stepLabels.map((lbl,i)=>`
      <div class="sim-prog-item ${i===App.simStep?'active':i<App.simStep?'done':''}">
        <div class="sim-prog-dot">${i<App.simStep?'✓':i+1}</div>
        <div class="sim-prog-lbl">${lbl}</div>
      </div>
      ${i<stepLabels.length-1?'<div class="sim-prog-line '+(i<App.simStep?'done':'')+'"></div>':''}`).join('')}
  </div>`;

  let body = '';
  if (App.simStep===0) body = simRenderStatus();
  else if (App.simStep===1) body = simRenderChoiceFilling();
  else if (App.simStep===2) body = simRenderAllotment();
  else body = simRenderProvisionalOrder();

  sim.innerHTML = indicator + body;
}

function simRenderStatus() {
  const p = App.profile;
  const rank = p.rank || '—';
  const _agg = calculateAggregate(p.maths, p.physics, p.chemistry);
  const agg  = _agg > 0 ? _agg.toFixed(1) : '—';
  const comm = p.category || '—';
  const cRank = p.rank ? Math.floor(p.rank * 0.42) : '—';
  const rnd = p.rank ? (1000000000 + Math.floor(p.rank * 12345) % 8999999999) : '—';
  return `
  <div class="sim-card">
    <div class="sim-gov-hdr"><div class="sim-gov-title">GOVERNMENT OF TAMIL NADU</div><div class="sim-gov-sub">TAMIL NADU ENGINEERING ADMISSIONS — 2026</div></div>
    <div class="sim-app-no">Application Number: ${p.applicationId||'Not entered'}</div>
    <div class="sim-status-grid">
      <div class="sim-status-row">
        <div class="sim-status-cell"><span>Community</span><strong>${comm}</strong></div>
        <div class="sim-status-cell"><span>Cutoff Marks</span><strong>${agg}</strong></div>
      </div>
      <div class="sim-status-row">
        <div class="sim-status-cell"><span>General Rank</span><strong>${rank}</strong></div>
        <div class="sim-status-cell"><span>Community Rank</span><strong>${cRank}</strong></div>
      </div>
      <div class="sim-status-row">
        <div class="sim-status-cell"><span>Random Number</span><strong>${rnd}</strong></div>
        <div class="sim-status-cell"><span>Upload Status</span><strong class="sim-ok">✅ Completed successfully</strong></div>
      </div>
      <div class="sim-status-row">
        <div class="sim-status-cell"><span>Is Eminent Sports Person</span><strong>No</strong></div>
        <div class="sim-status-cell"><span>Is Differently Abled Person</span><strong>No</strong></div>
      </div>
      <div class="sim-status-row">
        <div class="sim-status-cell"><span>Ex-Serviceman</span><strong>No</strong></div>
        <div class="sim-status-cell"><span>Certificate Verification Status</span><strong class="sim-ok">✅ Completed successfully</strong></div>
      </div>
    </div>
    ${!p.rank ? '<div class="sim-warn">⚠️ Enter your rank in Profile for accurate simulation</div>' : ''}
    <div class="sim-disclaimer">This is a simulation. Your actual status is on <a href="https://tneaonline.org" target="_blank">tneaonline.org ↗</a></div>
    <button class="btn-primary btn-glow btn-full" onclick="simGoToStep(1)" style="margin-top:20px">Proceed to Choice Filling →</button>
  </div>`;
}

function simRenderChoiceFilling() {
  const f = App.simFilter;
  const searchCol = (f.college||'').toLowerCase();
  const searchBr  = (f.branch||'').toLowerCase();
  const searchCat = f.category||'';

  const filtered = COLLEGES.filter(col => {
    if (searchCol && !col.name.toLowerCase().includes(searchCol)) return false;
    if (searchCat) { const t=simCollegeType(col.code); if(t!==searchCat) return false; }
    return true;
  }).slice(0,10);

  let rows = '';
  filtered.forEach(col => {
    SIM_BRANCHES.forEach(br => {
      if (searchBr && !br.name.toLowerCase().includes(searchBr)) return;
      const seats = simGetSeats(col.code, br.code);
      const sel = App.simChoices.find(c=>c.collegeCode===col.code&&c.branchCode===br.code);
      const safeColName = col.name.replace(/'/g,"\\'").replace(/"/g,'&quot;');
      const safeBrName  = br.name.replace(/'/g,"\\'");
      rows += `<tr class="${sel?'sim-row-sel':''}" onclick="simToggleChoice('${col.code}','${br.code}','${safeBrName}','${safeColName}')">
        <td><input type="checkbox" ${sel?'checked':''} onclick="event.stopPropagation();simToggleChoice('${col.code}','${br.code}','${safeBrName}','${safeColName}')"/></td>
        <td class="sim-order-cell">${sel?sel.order:''}</td>
        <td>${col.code}</td>
        <td class="sim-col-name">${col.name}</td>
        <td>${br.name}</td>
        <td class="${seats.oc===0?'sim-seat-zero':'sim-seat-ok'}">${seats.oc}</td>
        <td class="${seats.comm===0?'sim-seat-zero':'sim-seat-ok'}">${seats.comm}</td>
      </tr>`;
    });
  });

  const myChoicesHtml = App.simChoices.length>0 ? `
    <div class="sim-my-choices-list">
      ${App.simChoices.map(c=>`
        <div class="sim-choice-chip">
          <span>${c.order}. [${c.collegeCode}] ${c.collegeName.substring(0,28)}… — ${c.branchName.substring(0,20)}…</span>
          <button onclick="event.stopPropagation();simToggleChoice('${c.collegeCode}','${c.branchCode}','${c.branchName.replace(/'/g,"\\'")}','${c.collegeName.replace(/'/g,"\\'")}')">×</button>
        </div>`).join('')}
    </div>` : '<p style="font-size:13px;color:var(--text-muted);margin-top:8px">No choices selected yet. Check rows in the table below.</p>';

  return `
  <div class="sim-card">
    <div class="sim-gov-hdr"><div class="sim-gov-title">GOVERNMENT OF TAMIL NADU</div><div class="sim-gov-sub">TAMIL NADU ENGINEERING ADMISSIONS — 2026</div></div>
    <p style="font-size:13px;color:var(--text-muted);margin-bottom:16px">Fill your college-course choices in priority order. Choice 1 = your top preference. Reference: <a href="https://tneaonline.org" target="_blank" style="color:var(--accent)">tneaonline.org ↗</a></p>
    <div class="sim-filter-box">
      <div class="sim-filter-title">Filter Colleges</div>
      <div class="sim-filter-grid">
        <div><label>College Name:</label><input class="text-input" placeholder="e.g. Government College" value="${f.college||''}" oninput="App.simFilter.college=this.value;renderCounsellingSimulation()"/></div>
        <div><label>Branch Name:</label><input class="text-input" placeholder="e.g. Computer Science" value="${f.branch||''}" oninput="App.simFilter.branch=this.value;renderCounsellingSimulation()"/></div>
        <div><label>Category:</label>
          <select class="select-input" onchange="App.simFilter.category=this.value;renderCounsellingSimulation()">
            <option value="" ${!searchCat?'selected':''}>All Types</option>
            <option value="Govt" ${searchCat==='Govt'?'selected':''}>Government</option>
            <option value="Aided" ${searchCat==='Aided'?'selected':''}>Government Aided</option>
            <option value="Self-Financing" ${searchCat==='Self-Financing'?'selected':''}>Self-Financing</option>
          </select>
        </div>
      </div>
    </div>
    <div class="sim-table-toolbar">
      <span>Select a course — Academic</span>
      <div style="display:flex;align-items:center;gap:10px">
        <span class="sim-autosave">● Changes are auto saved.</span>
        ${App.simChoices.length>0?'<button class="btn-ghost" style="font-size:12px;padding:4px 10px" onclick="simClearChoices()">Clear All</button>':''}
      </div>
    </div>
    <div class="sim-table-wrap">
      <table class="sim-table">
        <thead>
          <tr>
            <th>Select</th><th>Choice order</th><th>College Code</th>
            <th>College Name</th><th>Branch Name</th>
            <th colspan="2" style="text-align:center">Seat Availability</th>
          </tr>
          <tr><th colspan="5"></th><th class="sim-seat-head">OC</th><th class="sim-seat-head">Comm.</th></tr>
        </thead>
        <tbody>${rows||'<tr><td colspan="7" style="text-align:center;padding:20px;color:var(--text-muted)">No results — try a different filter</td></tr>'}</tbody>
      </table>
    </div>
    <div class="sim-my-choices-section">
      <div style="display:flex;justify-content:space-between;align-items:center">
        <strong>My Choices List</strong>
        <span style="font-size:13px;color:var(--text-muted)">${App.simChoices.length} selected</span>
      </div>
      ${myChoicesHtml}
    </div>
    <div style="display:flex;gap:12px;margin-top:20px;flex-wrap:wrap">
      <button class="btn-ghost" onclick="simGoToStep(0)">← Back</button>
      <button class="btn-primary btn-glow" onclick="simLockAndAllot()" ${App.simChoices.length===0?'style="opacity:0.5;cursor:not-allowed"':''}>
        🔒 Lock Choices & Simulate Allotment
      </button>
    </div>
  </div>`;
}

function simRenderAllotment() {
  const allot = App.simAllotment;
  const p = App.profile;
  const rank = p.rank||'—';
  const cRank = p.rank ? Math.floor(p.rank*0.42) : '—';
  const comm = p.category||'OC';

  if (!allot) return `
  <div class="sim-card">
    <div class="sim-gov-hdr"><div class="sim-gov-title">GOVERNMENT OF TAMIL NADU</div><div class="sim-gov-sub">TAMIL NADU ENGINEERING ADMISSIONS — 2026</div></div>
    <div class="sim-no-allotment">
      <div style="font-size:48px;margin-bottom:12px">😔</div>
      <h3>No Seat Allotted in Round 1</h3>
      <p>Your rank is above the cutoff for all your selected choices. Add more colleges or try Round 2.</p>
      <div style="display:flex;gap:12px;margin-top:20px;justify-content:center;flex-wrap:wrap">
        <button class="btn-ghost" onclick="simGoToStep(1)">← Add More Choices</button>
        <button class="btn-outline" onclick="resetCounselling()">🔄 Restart</button>
      </div>
    </div>
  </div>`;

  const options = [
    { id:'accept',         label:'I accept and confirm the current allotment.', sub:'இப்போது எனக்கு ஒதுக்கப்பட்டதை நான் ஏற்று உறுதி செய்கிறேன்' },
    { id:'accept_upward',  label:'I accept the current allotment and opt for the upward movement. If allotted in upward movement, I confirm.', sub:'இப்போது எனக்கு ஒதுக்கப்பட்டதை நான் ஏற்கிறேன், ஆனால் மேல் முன்னுரிமை விருப்பங்களில் இடம் கிடைத்தால் அதை ஏற்று உறுதி செய்கிறேன்' },
    { id:'decline_upward', label:'I decline current allotment and opt for the upward movement. If not allotted in upward movement, move to the next round.', sub:'இப்போது எனக்கு ஒதுக்கப்பட்டதை நான் ஏற்கவில்லை, மேல் முன்னுரிமையில் இடம் கிடைக்கவில்லை என்றால் அடுத்த சுற்றுக்கு செல்கிறேன்' },
    { id:'decline_next',   label:'I decline current allotment and move to the next round to enable participation as per the vacancy position of the round.', sub:'இப்போது எனக்கு ஒதுக்கப்பட்டதை நான் ஏற்கவில்லை, அடுத்தகட்ட கலந்தாய்வில் சென்று தேர்வு உள்ள கல்லூரிகளுக்கு பங்கேற்க விரும்புகிறேன்' },
    { id:'decline_quit',   label:'I decline current allotment and quit counselling. I am aware that I cannot participate in further rounds of counselling.', sub:'இப்போது எனக்கு ஒதுக்கப்பட்டதை நான் ஏற்கவில்லை, நான் கலந்தாய்விலிருந்து வெளியேறுகிறேன்' },
  ];

  return `
  <div class="sim-card">
    <div class="sim-gov-hdr"><div class="sim-gov-title">GOVERNMENT OF TAMIL NADU</div><div class="sim-gov-sub">TAMIL NADU ENGINEERING ADMISSIONS — 2026</div></div>
    <div class="sim-allot-grid">
      <div class="sim-allot-cell"><span>Community</span><strong>${comm}</strong></div>
      <div class="sim-allot-cell"><span>General Rank</span><strong>${rank}</strong></div>
      <div class="sim-allot-cell"><span>Community Rank</span><strong>${cRank}</strong></div>
      <div class="sim-allot-cell"><span>Allotted Community</span><strong>${comm}</strong></div>
      <div class="sim-allot-cell"><span>Branch Name</span><strong>${allot.branchName}</strong></div>
      <div class="sim-allot-cell sim-allot-full"><span>College Name</span><strong>${allot.collegeCode} — ${allot.collegeName}</strong></div>
    </div>
    <div class="sim-options-title">Choose one of the options below:</div>
    <div class="sim-options-list">
      ${options.map((opt,i)=>`
        <label class="sim-opt-row">
          <input type="radio" name="simOption" value="${opt.id}" ${i===0?'checked':''}/>
          <div>
            <div class="sim-opt-en">${opt.label}</div>
            <div class="sim-opt-ta">${opt.sub}</div>
          </div>
        </label>`).join('')}
    </div>
    <div class="form-group" style="margin-top:20px">
      <label>Select Reporting TFC for tentative admission:</label>
      <select class="select-input full-width">
        <option value="">Select TFC...</option>
        ${TFC_LIST.map(t=>`<option>${t}</option>`).join('')}
      </select>
    </div>
    <div class="sim-confirm-note">⚠️ In the real portal, this action cannot be reversed. Here it's a simulation.</div>
    <div style="display:flex;gap:12px;margin-top:16px;flex-wrap:wrap">
      <button class="btn-ghost" onclick="simGoToStep(1)">← Back</button>
      <button class="btn-primary btn-glow" onclick="simConfirmAllotment()">Save →</button>
    </div>
  </div>`;
}

function simRenderProvisionalOrder() {
  const allot = App.simAllotment;
  const p = App.profile;
  const _agg2 = calculateAggregate(p.maths, p.physics, p.chemistry);
  const provAgg = _agg2 > 0 ? _agg2.toFixed(1) : '—';
  const today = new Date().toLocaleDateString('en-IN',{day:'2-digit',month:'2-digit',year:'numeric'});
  return `
  <div class="sim-card">
    <div class="sim-prov-wrap">
      <div class="sim-prov-title">TAMIL NADU ENGINEERING ADMISSIONS — 2026</div>
      <div class="sim-prov-sub">PROVISIONAL ALLOTMENT ORDER FOR B.E/B.TECH COURSES*</div>
      <div class="sim-prov-ref">Ref.No. —/TNEA/2026 &nbsp;&nbsp; Date: ${today}</div>
      <p class="sim-prov-intro">The candidate is informed that he/she has been <strong>PROVISIONALLY</strong> allotted as per the option exercised for admissions to the First year Degree Course, College and Branch as detailed below.</p>
      <div class="sim-prov-grid">
        <div class="sim-prov-row"><span>Application No.</span><span>: ${p.applicationId||'—'}</span></div>
        <div class="sim-prov-row"><span>Name</span><span>: ${p.name||'—'}</span></div>
        <div class="sim-prov-row"><span>Community</span><span>: ${p.category||'OC'}</span></div>
        <div class="sim-prov-row"><span>Category</span><span>: ${allot?simCollegeType(allot.collegeCode):'—'}</span></div>
        <div class="sim-prov-row"><span>Course</span><span>: B.E/B.Tech</span></div>
        <div class="sim-prov-row"><span>Cutoff Mark</span><span>: ${provAgg}</span></div>
        <div class="sim-prov-row"><span>College Allotted</span><span>: ${allot?`${allot.collegeCode} — ${allot.collegeName}`:'—'}</span></div>
        <div class="sim-prov-row"><span>Branch Allotted</span><span>: ${allot?allot.branchName:'—'}</span></div>
        <div class="sim-prov-row"><span>Seat Allotted Category</span><span>: ${p.category||'OC'} ACADEMIC</span></div>
      </div>
      <p class="sim-prov-disclaimer">* This is a <strong>simulation only</strong>. Your actual allotment order will be on <a href="https://tneaonline.org" target="_blank">tneaonline.org</a></p>
    </div>
    <div style="display:flex;gap:12px;margin-top:20px;justify-content:center;flex-wrap:wrap">
      <button class="btn-outline" onclick="resetCounselling()">🔄 Restart Simulation</button>
    </div>
  </div>`;
}

function advanceCounselling() { App.simStep = Math.min(App.simStep+1,3); renderCounsellingSimulation(); }
function resetCounselling() {
  App.simStep=0; App.simChoices=[]; App.simAllotment=null;
  App.simFilter={ college:'', branch:'', category:'' };
  renderCounsellingSimulation();
}

// ============================================================
// UPGRADE MODAL
// ============================================================
function showUpgradeModal(source) {
  const reasons = {
    'nav':          'Upgrade to Premium for rank prediction, AI Choice List and counselling simulation.',
    'rank':         '🏆 Rank Prediction & Verification requires Premium access.',
    'choice':       '📋 AI Choice List is a Premium-only feature.',
    'counselling':  '🎓 Full Counselling Simulation is available for Premium users only.',
    'result':       '🚀 See all college-course combinations with detailed probabilities.',
    'tier':         'Get complete TNEA counselling intelligence for just ₹149.',
    'cta':          'Students with Premium made 3x better college choices.',
    'marks-update': '📝 Marks update after board results requires Premium access.',
    'colleges':     '🏛️ Add unlimited colleges with Premium. Search all 550+ colleges.',
  };
  const el = document.getElementById('upgradeReason');
  const sl = document.getElementById('slotsLeft');
  if (el) el.textContent = reasons[source] || 'Unlock full Premium access for ₹149.';
  if (sl) sl.textContent = App.slotsLeft;
  document.getElementById('upgradeModal')?.classList.remove('hidden');
}

function closeUpgradeModal() {
  document.getElementById('upgradeModal')?.classList.add('hidden');
}

function initiatePayment() {
  closeUpgradeModal();
  const agg     = calculateAggregate(App.profile.maths||0, App.profile.physics||0, App.profile.chemistry||0);
  const content = document.getElementById('payConfirmContent');
  if (content) {
    content.innerHTML = `
      <table style="width:100%;border-collapse:collapse;font-size:14px">
        <tr><td style="padding:10px 0;color:var(--text-muted);border-bottom:1px solid var(--border)">Name</td>
            <td style="padding:10px 0;font-weight:600;text-align:right;border-bottom:1px solid var(--border)">${App.profile.name||'—'}</td></tr>
        <tr><td style="padding:10px 0;color:var(--text-muted);border-bottom:1px solid var(--border)">Email</td>
            <td style="padding:10px 0;font-weight:600;text-align:right;border-bottom:1px solid var(--border)">${App.profile.email||'—'}</td></tr>
        <tr><td style="padding:10px 0;color:var(--text-muted);border-bottom:1px solid var(--border)">Mathematics</td>
            <td style="padding:10px 0;font-weight:600;text-align:right;border-bottom:1px solid var(--border)">${App.profile.maths??'—'} / 100</td></tr>
        <tr><td style="padding:10px 0;color:var(--text-muted);border-bottom:1px solid var(--border)">Physics</td>
            <td style="padding:10px 0;font-weight:600;text-align:right;border-bottom:1px solid var(--border)">${App.profile.physics??'—'} / 100</td></tr>
        <tr><td style="padding:10px 0;color:var(--text-muted);border-bottom:1px solid var(--border)">Chemistry</td>
            <td style="padding:10px 0;font-weight:600;text-align:right;border-bottom:1px solid var(--border)">${App.profile.chemistry??'—'} / 100</td></tr>
        <tr><td style="padding:14px 0;font-weight:700;font-size:15px">TNEA Aggregate</td>
            <td style="padding:14px 0;font-weight:900;color:var(--accent);font-size:24px;text-align:right">${agg>0?agg:'—'} / 200</td></tr>
      </table>
      <div style="font-size:12px;color:var(--text-muted);margin-top:8px;text-align:center">
        Marks are locked after payment · Update costs ₹25
      </div>`;
  }
  document.getElementById('payConfirmModal')?.classList.remove('hidden');
}

function closePayConfirm() {
  document.getElementById('payConfirmModal')?.classList.add('hidden');
}

async function confirmPayment() {
  closePayConfirm();
  if (!App.currentUser) {
    showError('Please log in before making a payment.');
    navigateTo('auth');
    return;
  }
  showLoader();
  try {
    const res  = await authenticatedFetch(`${API_BASE}/payment/create-order`, { method: 'POST' });
    let data;
    try { data = await res.json(); } catch(e) { data = {}; }
    if (!res.ok) {
      showError(data.detail || 'Could not start payment. Please try again.');
      return;
    }
    if (!data.order_id || !data.key_id) {
      showError('Payment setup failed — missing order info. Please try again.');
      return;
    }

    const rzp = new Razorpay({
      key:         data.key_id,
      amount:      data.amount,
      currency:    data.currency,
      order_id:    data.order_id,
      name:        'PickMySeat',
      description: 'Premium Access — One Time',
      prefill: {
        name:  data.user_name  || '',
        email: data.user_email || ''
      },
      theme: { color: '#6C63FF' },
      handler: async function (response) {
        await verifyPayment(response);
      },
      modal: {
        ondismiss: function() {
          showToast('Payment cancelled', 'error');
        }
      }
    });
    rzp.open();
  } catch (e) {
    showError('Network error. Please check your internet connection and retry.');
  } finally {
    hideLoader();
  }
}

async function verifyPayment(response) {
  try {
    const res = await authenticatedFetch(`${API_BASE}/payment/verify`, {
      method: 'POST',
      body: JSON.stringify({
        razorpay_payment_id: response.razorpay_payment_id,
        razorpay_order_id:   response.razorpay_order_id,
        razorpay_signature:  response.razorpay_signature
      })
    });
    const data = await res.json();
    if (!res.ok) { showError('Payment verification failed. Contact support.pickmyseat@gmail.com'); return; }
    App.profile.grade = '1';
    handlePaymentSuccess(response.razorpay_payment_id);
  } catch (e) {
    showError('Payment verification failed. Contact support.pickmyseat@gmail.com');
  }
}

function handlePaymentSuccess(paymentId) {
  App.profile.hasPaid     = true;
  App.profile.marksLocked = true;
  App.userGrade           = 1;
  App.slotsLeft           = Math.max(0, App.slotsLeft - 1);
  // FIRESTORE: db.collection('users').doc(uid).update({ has_paid:true, razorpay_payment_id:paymentId })
  showToast('🎉 Premium unlocked! Welcome to full access.', 'success', 5000);
  setTimeout(() => navigateTo('dashboard'), 1000);
}

// ============================================================
// COOKIES
// ============================================================
function setCookie(name, value, days) {
  const exp = new Date();
  exp.setTime(exp.getTime() + days * 24 * 60 * 60 * 1000);
  document.cookie = `${name}=${value};expires=${exp.toUTCString()};path=/`;
}

function getCookie(name) {
  const eq = name + '=';
  return document.cookie.split(';')
    .map(c => c.trim())
    .find(c => c.startsWith(eq))
    ?.substring(eq.length) || null;
}

// ============================================================
// AUTHENTICATED FETCH HELPER
// ============================================================
async function authenticatedFetch(url, options = {}) {
  const token = localStorage.getItem('token');
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return fetch(url, { ...options, headers });
}

// ============================================================
// SESSION PERSISTENCE — /auth/me on page load
// ============================================================
async function restoreSessionFromToken() {
  const token = localStorage.getItem('token');
  if (!token) {
    App.currentUser = null;
    App.userGrade   = 3;
    App.profile     = {
      name:'', email:'', mobile:'', category:'',
      maths:null, physics:null, chemistry:null,
      marksLocked:false, rank:null, rankPhase:'pre',
      hasPaid:false, preferredColleges:[], preferredCourses:[],
    };
    updateNav();
    return;
  }
  try {
    const res = await authenticatedFetch(`${API_BASE}/auth/me`);
    if (res.status === 401) {
      localStorage.removeItem('token');
      return;
    }
    if (!res.ok) return;
    const data = await res.json();
    App.currentUser = {
      email: data.email,
      name: data.name,
      hasPaid: data.grade === '1',
    };
    App.profile.email        = data.email || '';
    App.profile.name         = data.name  || '';
    App.profile.mobile       = data.mobile || '';
    App.profile.category     = data.community || '';
    App.profile.maths        = data.maths;
    App.profile.physics      = data.physics;
    App.profile.chemistry    = data.chemistry;
    App.profile.marksLocked  = data.marks_locked || false;
    App.profile.rank         = data.rank;
    App.profile.rankPhase    = data.rank_phase || 'pre';
    App.profile.hasPaid      = data.grade === '1';
    App.userGrade            = data.grade === '1' ? 1 : 2;
App.profile.preferredColleges = data.preferred_colleges ? JSON.parse(data.preferred_colleges) : [];
    App.profile.preferredCourses  = data.preferred_courses  ? JSON.parse(data.preferred_courses)  : [];
    App.profile.applicationId = data.application_id || '';

    // Auto-clear stale course codes from pre-fix data
    if (App.profile.preferredCourses.length > 0 && BRANCHES.length > 0) {
      const validCodes = new Set(BRANCHES.map(b => b.code));
      const hasStale = App.profile.preferredCourses.some(c => !c.code || !validCodes.has(c.code));
      if (hasStale) {
        App.profile.preferredCourses = [];
        authenticatedFetch(`${API_BASE}/auth/update-profile`, {
          method: 'POST',
          body: JSON.stringify({
            preferred_colleges: App.profile.preferredColleges,
            preferred_courses: []
          })
        }).catch(() => {});
        setTimeout(() => showToast('Course preferences were reset after a system update — please re-add them in Profile', 'warning'), 2000);
      }
    }

    updateNav();
    prefillAndLockMarks();
  } catch (e) {
    // silently fail if session restore errors
  }
}


async function checkRankListStatus() {
  try {
    const res  = await fetch(`${API_BASE}/config`);
    const data = await res.json();
    App.rankListReleased = data.rank_list_released || false;
    const banner = document.getElementById('rankListBanner');
    if (banner && data.rank_list_released) {
      banner.classList.remove('hidden');
      banner.innerHTML = `
        <div style="background:linear-gradient(135deg,#6C63FF,#8B5CF6);color:white;padding:14px 24px;text-align:center;font-weight:600;font-size:14px;position:relative;z-index:1001">
          🏆 2026 TNEA Rank List is out! Enter your Application ID and Rank for accurate predictions.
          <button onclick="navigateTo('profile')" style="margin-left:12px;background:white;color:#6C63FF;border:none;padding:6px 14px;border-radius:6px;font-weight:700;cursor:pointer">
            Update Now →
          </button>
        </div>`;
    }
  } catch(e) {
    App.rankListReleased = false;
  }
}

async function verifyAndSaveRank() {
  const appId = document.getElementById('profileAppId')?.value?.trim();
  const rank  = parseInt(document.getElementById('profileRankVerify')?.value);
  const name  = App.profile.name || '';

  if (!appId) { showToast('Please enter your Application ID', 'error'); return; }
  if (!rank)  { showToast('Please enter your rank', 'error'); return; }

  const btn = document.querySelector('#profileAppIdSection .btn-primary');
  if (btn) { btn.disabled = true; btn.textContent = 'Verifying...'; }

  showLoader();
  try {
    const res  = await authenticatedFetch(`${API_BASE}/predict/verify-rank`, {
      method: 'POST',
      body: JSON.stringify({ application_id: appId, name, rank })
    });
    const data = await res.json();

    const statusEl = document.getElementById('rankVerifyStatus');
    if (!res.ok) {
      if (statusEl) {
        statusEl.classList.remove('hidden');
        statusEl.style.cssText = 'background:rgba(239,68,68,0.1);border:1px solid var(--error);color:var(--error);margin-top:12px;padding:12px;border-radius:8px;font-size:13px;font-weight:600';
        statusEl.textContent = `❌ ${data.detail}`;
      }
      return;
    }

    App.profile.applicationId = appId;
    App.profile.rank          = data.rank;

    if (statusEl) {
      statusEl.classList.remove('hidden');
      statusEl.style.cssText = 'background:rgba(16,185,129,0.1);border:1px solid var(--success);color:var(--success);margin-top:12px;padding:12px;border-radius:8px;font-size:13px;font-weight:600';
      statusEl.textContent = `✅ Rank #${data.rank.toLocaleString()} verified! Your predictions are now based on your official rank.`;
    }

    showToast(`Rank ${data.rank.toLocaleString()} verified ✅`, 'success');
    setTimeout(() => navigateTo('dashboard'), 1500);

  } catch(e) {
    showError('No connection. Check your internet and retry.');
  } finally {
    hideLoader();
    if (btn) { btn.disabled = false; btn.textContent = '✅ Verify My Rank'; }
  }
}
// ============================================================
// INIT
// ============================================================
document.addEventListener('DOMContentLoaded', async () => {
  await loadCollegesAndBranches();
  initTheme();
  await restoreSessionFromToken();
  await checkRankListStatus();
  navigateTo('landing');
});