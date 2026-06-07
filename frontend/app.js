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
  liveCount:       342,
  slotsLeft:       23,
  rankPhase:       'pre',
  counsellingStep: 0,
  theme:           'dark',

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
const COLLEGES = [
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
function initTheme() {
  const saved = localStorage.getItem('pms_theme') || 'dark';
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
function buildCollegeSearchDropdown(containerId, onSelect, placeholder = 'Search by name or code...') {
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
      list.innerHTML = colleges.slice(0, 50).map(c => `
        <div class="college-option" onclick="selectCollegeOption('${containerId}', '${c.code}')">
          <span class="college-code-tag">${c.code}</span>
          <span class="college-option-name">${c.name}</span>
        </div>`).join('');
      if (colleges.length > 50) {
        list.innerHTML += `<div class="college-more-note">Showing 50 of ${colleges.length}. Type more to narrow down.</div>`;
      }
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
function navigateTo(page) {
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
  if (page === 'profile')      renderProfile();
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
  } else {
    navUser.classList.add('hidden');
    navLogin.classList.remove('hidden');
    navUpgrade.classList.add('hidden');
    navDash.classList.add('hidden');
    navProf.classList.add('hidden');
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
function showToast(msg, type = 'info', duration = 3000) {
  const toast = document.getElementById('toast');
  toast.textContent = msg;
  toast.className = `toast show ${type}`;
  setTimeout(() => toast.classList.remove('show'), duration);
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
  };
  update();
  setInterval(() => {
    if (Math.random() > 0.7) { App.liveCount++; update(); }
  }, 8000);
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

// College prestige tier based on code prefix — adjusts cutoff
function getCollegeTierAdjust(code) {
  const c = parseInt(code);
  // Top government autonomous
  if (['0001','0002','0003','0004','2006','2007','5008'].includes(code)) return 10;
  // Government
  if (c < 2000 && c >= 1000) return -5;  // Chennai region private
  if (code.startsWith('2') && c < 2100) return 0;  // government/aided
  if (code.startsWith('2') && c >= 2600) return -8; // Salem/Namakkal belt
  if (code.startsWith('2') && c >= 2700) return -5; // Coimbatore private
  if (code.startsWith('3')) return -10;  // Trichy/Thanjavur region
  if (code.startsWith('4')) return -12;  // South TN
  if (code.startsWith('5')) return -10;  // Madurai/Dindigul
  return -5;
}

function predictProbability(aggregate, collegeCode, courseName) {
  const course = DATA.courses.find(c => c.name === courseName);
  if (!course) return 50;

  const tierAdj = getCollegeTierAdjust(collegeCode);
  const cutoff  = course.cutoffBase + tierAdj;
  const diff    = parseFloat(aggregate) - cutoff;

  let prob;
  if      (diff >= 15)  prob = 90 + Math.min(9, diff - 15);
  else if (diff >= 8)   prob = 75 + (diff - 8) * 2;
  else if (diff >= 0)   prob = 55 + diff * 2.5;
  else if (diff >= -8)  prob = 40 + (diff + 8) * 2;
  else if (diff >= -15) prob = 20 + (diff + 15) * 3;
  else                  prob = Math.max(3, 20 + diff);

  return Math.round(Math.min(99, Math.max(2, prob)));
}

function getLastYearCutoff(collegeCode, courseName) {
  const course = DATA.courses.find(c => c.name === courseName);
  if (!course) return '—';
  return (course.cutoffBase + getCollegeTierAdjust(collegeCode)).toFixed(1);
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
  buildCollegeSearchDropdown('freeCollegeSearchContainer', (college) => {
    freeSelectedCollege = college;
  }, 'Search college by name or code...');

  populateAllCourses('freeCourse');
  document.getElementById('freeResultCard').classList.add('hidden');
}

function populateAllCourses(selectId) {
  const sel = document.getElementById(selectId);
  if (!sel) return;
  sel.innerHTML = '<option value="">Select a course...</option>';
  DATA.courses.forEach(c => {
    const opt = document.createElement('option');
    opt.value = c.name; opt.textContent = c.name; sel.appendChild(opt);
  });
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
  if (!freeSelectedCollege) {
    showToast('Please select a college', 'error'); return;
  }
  if (!course) {
    showToast('Please select a course', 'error'); return;
  }



  renderFreeResult({
    agg, prob, rankBand, cutoff,
    college: `[${freeSelectedCollege.code}] ${freeSelectedCollege.name}`,
    course
  });

  setCookie('pms_free_used', '1', 7);

  // Disable form
  document.getElementById('freePredictForm')
    ?.querySelectorAll('input,select').forEach(el => el.disabled = true);
  const btn = document.querySelector('#freePredictForm .predict-btn');
  if (btn) btn.disabled = true;
  const bar = document.getElementById('cookieUsageBar');
  if (bar) bar.textContent = '🔒 Free prediction used · Login to predict more';
}

function renderFreeResult({ agg, prob, rankBand, cutoff, college, course }) {
  document.getElementById('resultCollegeName').textContent = college;
  document.getElementById('resultCourseName').textContent  = course;
  document.getElementById('resultAggregate').textContent   = `${agg} / 200`;
  document.getElementById('resultCutoff').textContent      = cutoff;
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
  try {
    const res  = await fetch(`${API_BASE}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });
    const data = await res.json();
    if (!res.ok) { showToast(data.detail || 'Login failed', 'error'); return; }
    localStorage.setItem('token', data.token);
    simulateLogin({ email, name: data.name, hasPaid: data.grade === '1' });
  } catch(e) {
    showToast('Server error. Try again.', 'error');
  }
}

async function signupUser() {
  const name     = document.getElementById('signupName')?.value?.trim();
  const email    = document.getElementById('signupEmail')?.value?.trim();
  const mobile   = document.getElementById('signupMobile')?.value?.trim();
  const password = document.getElementById('signupPassword')?.value;
  const category = document.getElementById('signupCategory')?.value || 'OC';
  if (!name || !email || !mobile || !password) {
    showToast('Please fill all fields', 'error'); return;
  }
  if (password.length < 8) {
    showToast('Password must be at least 8 characters', 'error'); return;
  }
  try {
    const res  = await fetch(`${API_BASE}/auth/signup`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, name, mobile, community: category })
    });
    const data = await res.json();
    if (!res.ok) { showToast(data.detail || 'Signup failed', 'error'); return; }
    localStorage.setItem('token', data.token);
    simulateLogin({ email, name: data.name, hasPaid: false });
  } catch(e) {
    showToast('Server error. Try again.', 'error');
  }
}

function loginGoogle() {
  // FIREBASE: firebase.auth().signInWithPopup(new firebase.auth.GoogleAuthProvider())
  simulateLogin({ email:'demo@gmail.com', name:'Demo Student', hasPaid:false });
}

function simulateLogin(userData) {
  App.currentUser     = userData;
  App.profile.email   = userData.email  || '';
  App.profile.name    = userData.name   || '';
  App.profile.mobile  = userData.mobile || '';
  App.profile.hasPaid = userData.hasPaid || false;
  App.userGrade       = userData.hasPaid ? 1 : 2;
  showToast(`Welcome${userData.name ? ', ' + userData.name.split(' ')[0] : ''}! 🎉`, 'success');
  navigateTo('profile');
}

function logout() {
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

  document.getElementById('profileName').value     = App.profile.name     || '';
  document.getElementById('profileEmail').value    = App.profile.email    || '';
  document.getElementById('profileMobile').value   = App.profile.mobile   || '';
  document.getElementById('profileCategory').value = App.profile.category || '';

  const locked = App.profile.marksLocked;
  document.getElementById('marksLockedBanner')?.classList.toggle('hidden', !locked);

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
    if (locked) {
      marksLockNote.classList.remove('hidden');
      marksLockNote.textContent = '🔒 Marks locked — contact support to update';
    } else {
      marksLockNote.classList.add('hidden');
    }
  }

  updateProfileAggregate();

  document.getElementById('profileRankSection')
    ?.classList.toggle('hidden', App.userGrade !== 1);

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
function renderPreferredColleges() {
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

function renderPreferredCourses() {
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
            <div class="slot-sub">${course.dept}</div>
          </div>
          <button class="slot-remove" onclick="removePreferredCourse(${i})">✕</button>
        </div>`;
    } else if (i === App.profile.preferredCourses.length) {
      grid.innerHTML += `
        <div class="preferred-slot add-slot">
          <select class="select-input" onchange="addPreferredCourse(this.value);this.value=''">
            <option value="">+ Add Course ${i+1}</option>
            ${DATA.courses.map(c=>`<option value="${c.id}">${c.name}</option>`).join('')}
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
  showToast(`[${college.code}] ${college.name} added ✅`, 'success');
}

function removePreferredCollege(i) {
  App.profile.preferredColleges.splice(i,1);
  renderPreferredColleges();
}

function addPreferredCourse(id) {
  if (!id) return;
  const course = DATA.courses.find(c => c.id === id);
  if (!course) return;
  if (App.profile.preferredCourses.find(c => c.id === id)) {
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

function saveProfile() {
  const name  = document.getElementById('profileName')?.value?.trim();
  const email = document.getElementById('profileEmail')?.value?.trim();

  if (!name)  { showToast('Please enter your name','error');  return; }
  if (!email) { showToast('Please enter your email','error'); return; }

  App.profile.name     = name;
  App.profile.email    = email;
  App.profile.mobile   = document.getElementById('profileMobile')?.value?.trim()    || '';
  App.profile.category = document.getElementById('profileCategory')?.value          || '';

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

  // FIRESTORE: db.collection('users').doc(uid).set({...App.profile},{merge:true})
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

function confirmMarksUpdate() {
  const m = parseFloat(document.getElementById('updateMath')?.value)     || null;
  const p = parseFloat(document.getElementById('updatePhysics')?.value)  || null;
  const c = parseFloat(document.getElementById('updateChemistry')?.value)|| null;
  if (!m || !p || !c) { showToast('Please enter all three marks','error'); return; }
  if (m>100 || p>100 || c>100) { showToast('Each mark must be 0–100','error'); return; }
  // RAZORPAY ₹25: new Razorpay({ key:'...', amount:2500, ... }).open()
  App.profile.maths     = m;
  App.profile.physics   = p;
  App.profile.chemistry = c;
  App.profile.marksLocked = true;
  closeMarksUpdate();
  showToast('Marks updated successfully ✅','success');
  renderDashboard();
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
    </div>
    <div class="agg-formula">
      = (${App.profile.maths||'M'}/2) + (${App.profile.physics||'P'}/4) + (${App.profile.chemistry||'C'}/4) × 2
    </div>`;
}

function renderComboProbCards() {
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

  const agg = calculateAggregate(
    App.profile.maths||0, App.profile.physics||0, App.profile.chemistry||0
  );
  const combos = [];
  colleges.forEach(college => {
    courses.forEach(course => {
      combos.push({ college, course, prob: predictProbability(agg, college.code, course.name) });
    });
  });
  combos.sort((a,b) => b.prob - a.prob);

  grid.innerHTML = combos.map(combo => {
    const pc     = getProbClass(combo.prob);
    const cutoff = getLastYearCutoff(combo.college.code, combo.course.name);
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
            <div class="combo-prob-label">Probability · Cutoff: ${cutoff}</div>
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
        ${DATA.courses.map(c=>`<option value="${c.name}">${c.name}</option>`).join('')}
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

  populateAllCourses('premiumCourseSelect');
}

function runPremiumQuickPredict() {
  const wrap   = document.getElementById('premiumSearchWrap');
  const course = document.getElementById('premiumCourseSelect')?.value;
  const college= wrap?._selectedCollege;

  if (!college) { showToast('Please select a college', 'error'); return; }
  if (!course)  { showToast('Please select a course',  'error'); return; }

  const agg  = calculateAggregate(
    App.profile.maths||0, App.profile.physics||0, App.profile.chemistry||0
  );

  if (agg === 0) {
    showToast('Please add your marks in Profile first', 'error'); return;
  }

  const prob   = predictProbability(agg, college.code, course);
  const cutoff = getLastYearCutoff(college.code, course);
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
          <div style="font-size:12px;color:var(--text-muted);margin-top:4px">Cutoff: ${cutoff} · Agg: ${agg}/200</div>
        </div>
        <div style="text-align:right">
          <div style="font-size:32px;font-weight:900;color:${prob>=65?'var(--success)':prob>=35?'var(--warning)':'var(--danger)'}">
            ${prob}%
          </div>
          <span class="combo-status-tag ${pc.statusCls}">${pc.status}</span>
        </div>
      </div>`;
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

function renderRankCard() {
  const card = document.getElementById('dashRankCard');
  if (!card) return;
  const agg      = calculateAggregate(App.profile.maths||0, App.profile.physics||0, App.profile.chemistry||0);
  const rankBand = predictRankBand(agg);
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

function renderChoiceList() {
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

  const agg = calculateAggregate(App.profile.maths||0, App.profile.physics||0, App.profile.chemistry||0);
  const combos = [];
  colleges.forEach(college => {
    courses.forEach(course => {
      combos.push({ college, course, prob: predictProbability(agg, college.code, course.name) });
    });
  });
  combos.sort((a,b) => b.prob - a.prob);

  const viable   = combos.filter(c => c.prob >= 35);
  const unlikely = combos.filter(c => c.prob <  35);

  wrap.innerHTML = `
    <div style="font-size:12px;color:var(--text-muted);margin-bottom:16px;font-style:italic;padding:10px 14px;background:var(--surface2);border-radius:8px">
      🤖 AI-generated priority order based on your marks and TNEA 2021–2024 cutoff data.
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
      </div>` : ''}`;
}

function renderCounsellingSimulation() {
  const sim = document.getElementById('counsellingSim');
  if (!sim) return;
  const steps = [
    { icon:'📝', title:'Registration',         desc:'Online registration on tnea.ac.in with your board roll number, date of birth and marks.' },
    { icon:'✅', title:'Rank Publication',      desc:'TNEA publishes your rank. Compare it here against our AI prediction for accuracy.' },
    { icon:'📋', title:'Choice Filling',        desc:'Fill college-course choices in priority order. Use your AI Choice List above for best results.' },
    { icon:'🔒', title:'Choice Locking',        desc:'Lock your list before the deadline. No changes allowed after locking.' },
    { icon:'🏛️', title:'Round 1 Allotment',     desc:'Seats allotted based on rank and choices. AI predicts your most likely allotment.' },
    { icon:'🎯', title:'Acceptance / Upgrade',  desc:'Accept current seat or wait for Round 2 for a potentially better option.' },
    { icon:'🎓', title:'Reporting to College',  desc:'Report to allotted college with originals. Admission confirmed.' },
  ];
  sim.innerHTML = `
    <div class="sim-steps">
      ${steps.map((step,idx) => `
        <div class="sim-step ${idx===App.counsellingStep?'active':idx<App.counsellingStep?'done':''}">
          <div class="sim-step-icon">${idx<App.counsellingStep?'✅':step.icon}</div>
          <div>
            <div class="sim-step-title">Step ${idx+1}: ${step.title}</div>
            <div class="sim-step-desc">${step.desc}</div>
          </div>
        </div>`).join('')}
    </div>
    <div style="margin-top:20px;display:flex;align-items:center;gap:16px">
      ${App.counsellingStep < steps.length-1
        ? `<button class="btn-primary" onclick="advanceCounselling()">Simulate Next Step →</button>`
        : `<button class="btn-outline" onclick="resetCounselling()">🔄 Restart Simulation</button>`}
      <span style="font-size:13px;color:var(--text-muted)">
        Step ${App.counsellingStep+1} of ${steps.length}
      </span>
    </div>`;
}

function advanceCounselling() { App.counsellingStep++; renderCounsellingSimulation(); }
function resetCounselling()   { App.counsellingStep=0; renderCounsellingSimulation(); }

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

function confirmPayment() {
  closePayConfirm();
  // RAZORPAY PLACEHOLDER:
  // new Razorpay({ key:'YOUR_KEY', amount:14900, currency:'INR',
  //   name:'PickMySeat.AI', description:'Premium Access',
  //   handler:(r) => handlePaymentSuccess(r.razorpay_payment_id)
  // }).open();
  handlePaymentSuccess('pay_demo_' + Date.now());
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
  if (!token) return;
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
    updateNav();
  } catch (e) {
    // silently fail if session restore errors
  }
}

// ============================================================
// INIT
// ============================================================
document.addEventListener('DOMContentLoaded', async () => {
  initTheme();
  await restoreSessionFromToken();
  navigateTo('landing');
  // FIREBASE: firebase.auth().onAuthStateChanged(user => { ... })
});