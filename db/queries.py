"""
Organised by business domain:
    • Customer Management
    • Substation Management
    • Meter Management
    • Power Source Management
    • Outage Analysis
    • Maintenance Analysis
    • Revenue Analysis
    • Consumption Trend Analysis
"""

from db.connection import get_connection

# ═══════════════════════════════════════════════════════════════════════
# HELPER
# ═══════════════════════════════════════════════════════════════════════

def _run(query, params=None, conn=None):
    """
    Execute *query* with *params* and return (column_names, rows).
    Opens (and closes) its own connection when *conn* is None.
    """
    own_conn = conn is None
    if own_conn:
        conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SET search_path TO electricity_grid_management;")
        cur.execute(query, params or ())
        columns = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
        cur.close()
        return columns, rows
    finally:
        if own_conn:
            conn.close()


# ═══════════════════════════════════════════════════════════════════════
# 1 · CUSTOMER MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════

def get_all_pin_codes(conn=None):
    """Q1 — Retrieve all pin codes with city, district, and state."""
    return _run("SELECT * FROM Pin_Code;", conn=conn)


def count_customers_per_pin_code(conn=None):
    """Q2 — Count the number of customers for every pin code."""
    return _run("""
        SELECT c.pin_code, COUNT(c.Customer_ID) AS customer_count
        FROM Customer c
        GROUP BY c.pin_code
        ORDER BY customer_count DESC;
    """, conn=conn)


def find_customers_by_pin_and_status(pin_code, status="Connected", conn=None):
    """Q3 — Find customers (with meter) in a given pin code filtered by connection status."""
    return _run("""
        SELECT c.Customer_ID, c.Customer_Name, c.Phone_Number,
               c.Block_Flat_No, c.Street, m.Meter_ID
        FROM Customer c
        JOIN Meter m ON c.Customer_ID = m.Customer_ID
        WHERE c.Pin_Code = %s AND c.Connection_Status = %s;
    """, (pin_code, status), conn=conn)


def customer_distribution_by_type_and_region(conn=None):
    """Q21 — Customer distribution by customer type in every city/district."""
    return _run("""
        SELECT ct.Type_Name AS customer_type,
               p.City, p.District,
               COUNT(c.Customer_ID) AS customer_count
        FROM Customer c
        JOIN Customer_Type ct ON c.Customer_Type_ID = ct.Customer_Type_ID
        JOIN Pin_Code p        ON c.Pin_Code = p.Pin_Code
        GROUP BY ct.Customer_Type_ID, p.City, p.District
        ORDER BY customer_count DESC;
    """, conn=conn)


def customers_with_meter_before_date(cutoff_date="2019-01-01", conn=None):
    """Q22 — Number of customers per state whose meter was installed before a date."""
    return _run("""
        SELECT pc.State, COUNT(cu.Customer_ID) AS customer_count
        FROM Meter me
        JOIN Customer cu ON me.Customer_ID = cu.Customer_ID
        JOIN Pin_Code pc ON cu.Pin_Code   = pc.Pin_Code
        WHERE me.Installation_Date < %s
        GROUP BY pc.State
        ORDER BY customer_count DESC;
    """, (cutoff_date,), conn=conn)


def connected_customers_per_city(state="GUJARAT", conn=None):
    """Q24 — Count of connected customers in each city within a state."""
    return _run("""
        SELECT COUNT(c.Customer_ID) AS number_of_customers,
               p.City, p.State
        FROM Customer c
        NATURAL JOIN Pin_Code p
        WHERE c.Connection_Status = 'Connected' AND p.State = %s
        GROUP BY p.City, p.State
        ORDER BY number_of_customers DESC;
    """, (state,), conn=conn)


# ═══════════════════════════════════════════════════════════════════════
# 2 · SUBSTATION MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════

def substations_in_pin_code(pin_code, conn=None):
    """Q4 — All substations located in a given pin code."""
    return _run("""
        SELECT s.Substation_ID, s.Area, s.Status, s.Capacity
        FROM Substation s
        JOIN Pin_Code p ON s.Pin_Code = p.Pin_Code
        WHERE p.Pin_Code = %s;
    """, (pin_code,), conn=conn)


def active_meters_in_large_substations(min_feeders=4, conn=None):
    """Q18 — Active meters in substations that have more than N feeders."""
    return _run("""
        SELECT m.Meter_ID, m.Current_Reading, s.Substation_ID
        FROM Meter m
        JOIN Feeder f    ON m.Feeder_ID    = f.Feeder_ID
        JOIN Substation s ON f.Substation_ID = s.Substation_ID
        WHERE s.Substation_ID IN (
            SELECT Substation_ID
            FROM Feeder
            GROUP BY Substation_ID
            HAVING COUNT(Feeder_ID) > %s
        ) AND m.Status = 'Active';
    """, (min_feeders,), conn=conn)


def connected_substations(substation_id, conn=None):
    """Q19 — Substations directly connected to a given substation."""
    return _run("""
        SELECT sc.Substation2_ID AS connected_substation
        FROM Substation_Connections sc
        WHERE sc.Substation1_ID = %s
        UNION
        SELECT sc.Substation1_ID
        FROM Substation_Connections sc
        WHERE sc.Substation2_ID = %s;
    """, (substation_id, substation_id), conn=conn)


def substations_by_circuit_breaker_type(conn=None):
    """Q30 — Number of substations grouped by circuit-breaker type."""
    return _run("""
        SELECT Circuit_Breakers,
               COUNT(Substation_ID) AS number_of_substations
        FROM Substation
        GROUP BY Circuit_Breakers
        ORDER BY number_of_substations DESC;
    """, conn=conn)


def substations_with_multiple_managers(conn=None):
    """Q31 — Substations where more than one employee has the 'Manager' role."""
    return _run("""
        SELECT Substation_ID, COUNT(Employee_ID) AS manager_count
        FROM Employee
        WHERE Role = 'Manager'
        GROUP BY Substation_ID
        HAVING COUNT(Employee_ID) > 1;
    """, conn=conn)


# ═══════════════════════════════════════════════════════════════════════
# 3 · METER MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════

def meters_by_customer_type_in_state(state="GUJARAT", conn=None):
    """Q23 — Count of meters in a state, categorised by customer type."""
    return _run("""
        SELECT COUNT(me.Meter_ID) AS number_of_meters, ct.Type_Name
        FROM Meter me
        NATURAL JOIN Customer cu
        NATURAL JOIN Customer_Type ct
        NATURAL JOIN Pin_Code pc
        WHERE pc.State = %s
        GROUP BY ct.Type_Name
        ORDER BY number_of_meters DESC;
    """, (state,), conn=conn)


# ═══════════════════════════════════════════════════════════════════════
# 4 · POWER SOURCE MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════

def power_sources_in_pin_code(pin_code, conn=None):
    """Q6 — Power sources in a given pin code."""
    return _run("""
        SELECT ps.Power_Source_ID, ps.Type, ps.Capacity, ps.Status
        FROM Power_Source ps
        WHERE ps.Pin_Code = %s;
    """, (pin_code,), conn=conn)


def power_sources_by_same_owner(power_source_id, conn=None):
    """Q13 — All power sources owned by the same owner as a given source."""
    return _run("""
        SELECT p2.Power_Source_ID, p2.Type, p2.Capacity, p2.Owner_ID
        FROM Power_Source p1
        JOIN Power_Source p2 ON p1.Owner_ID = p2.Owner_ID
        WHERE p1.Power_Source_ID = %s;
    """, (power_source_id,), conn=conn)


def total_capacity_by_state(conn=None):
    """Q15 — Total power-source capacity aggregated by state."""
    return _run("""
        SELECT p.State, SUM(ps.Capacity) AS total_capacity
        FROM Power_Source ps
        JOIN Pin_Code p ON ps.Pin_Code = p.Pin_Code
        GROUP BY p.State
        ORDER BY total_capacity DESC;
    """, conn=conn)


def total_capacity_by_source_type(conn=None):
    """Q16 — Total power-source capacity aggregated by source type."""
    return _run("""
        SELECT Type, SUM(Capacity) AS total_capacity
        FROM Power_Source
        GROUP BY Type
        ORDER BY total_capacity DESC;
    """, conn=conn)


def generation_by_active_owners(conn=None):
    """Q27 — Total power generation from each owner (active sources only)."""
    return _run("""
        SELECT pso.Name, SUM(ps.Generation_Data) AS total_generation
        FROM Power_Source ps
        JOIN Power_Source_Owner pso ON ps.Owner_ID = pso.Owner_ID
        WHERE ps.Status = 'Active'
        GROUP BY pso.Name
        ORDER BY total_generation DESC;
    """, conn=conn)


# ═══════════════════════════════════════════════════════════════════════
# 5 · OUTAGE ANALYSIS
# ═══════════════════════════════════════════════════════════════════════

def outages_in_pin_code(pin_code, conn=None):
    """Q7 — All outages with affected areas in a given pin code."""
    return _run("""
        SELECT o.Outage_ID, o.Outage_Type, o.Status, aa.Area
        FROM Outage o
        JOIN Affected_Area aa ON o.Outage_ID = aa.Outage_ID
        WHERE aa.Pin_Code = %s;
    """, (pin_code,), conn=conn)


def ongoing_outages_in_pin_code(pin_code, conn=None):
    """Q8 — Ongoing outages with affected areas in a given pin code."""
    return _run("""
        SELECT o.Outage_ID, o.Outage_Type, o.Status, aa.Area
        FROM Outage o
        LEFT JOIN Affected_Area aa ON o.Outage_ID = aa.Outage_ID
        WHERE aa.Pin_Code = %s AND o.Status = 'Ongoing';
    """, (pin_code,), conn=conn)


def total_outages_per_pin_code(conn=None):
    """Q9 — Total distinct outages per pin code."""
    return _run("""
        SELECT aa.Pin_Code,
               COUNT(DISTINCT o.Outage_ID) AS outage_count
        FROM Outage o
        LEFT JOIN Affected_Area aa ON o.Outage_ID = aa.Outage_ID
        GROUP BY aa.Pin_Code
        ORDER BY outage_count DESC;
    """, conn=conn)


def pin_codes_with_many_outages(start_date, end_date, threshold=0, conn=None):
    """Q12 — Pin codes having more than *threshold* outages in a date range."""
    return _run("""
        SELECT pc.Pin_Code, COUNT(o.Outage_ID) AS outage_count
        FROM Outage o
        NATURAL JOIN Affected_Area aa
        NATURAL JOIN Pin_Code pc
        WHERE o.Start_Date_Time BETWEEN %s AND %s
        GROUP BY pc.Pin_Code
        HAVING COUNT(o.Outage_ID) > %s
        ORDER BY outage_count DESC;
    """, (start_date, end_date, threshold), conn=conn)


def frequent_outage_areas_in_year(year=2020, conn=None):
    """Q34 — Areas hit more often than the average, with outage count and avg duration (hours)."""
    return _run("""
        WITH OutagesPerArea AS (
            SELECT aa.Area AS area_name,
                   COUNT(DISTINCT aa.Outage_ID) AS outage_count,
                   AVG(EXTRACT(EPOCH FROM (o.End_Date_Time - o.Start_Date_Time)) / 3600)
                       AS avg_outage_hours
            FROM Affected_Area aa
            JOIN Outage o ON o.Outage_ID = aa.Outage_ID
            WHERE EXTRACT(YEAR FROM o.Start_Date_Time) = %s
            GROUP BY aa.Area
        ),
        AverageOutagePerArea AS (
            SELECT AVG(outage_count) AS avg_outage
            FROM OutagesPerArea
        )
        SELECT opa.area_name, opa.outage_count,
               ROUND(opa.avg_outage_hours::numeric, 2) AS avg_duration_hrs
        FROM OutagesPerArea opa, AverageOutagePerArea avg
        WHERE opa.outage_count >= avg.avg_outage
        ORDER BY opa.area_name;
    """, (year,), conn=conn)


# ═══════════════════════════════════════════════════════════════════════
# 6 · MAINTENANCE ANALYSIS
# ═══════════════════════════════════════════════════════════════════════

def total_feeder_capacity_per_pin_code(conn=None):
    """Q5 — Sum of feeder load capacity aggregated by pin code."""
    return _run("""
        SELECT p.Pin_Code, SUM(f.Capacity) AS total_capacity
        FROM Feeder f
        JOIN Substation s ON f.Substation_ID = s.Substation_ID
        JOIN Pin_Code p   ON s.Pin_Code      = p.Pin_Code
        GROUP BY p.Pin_Code
        ORDER BY total_capacity DESC;
    """, conn=conn)


def overloaded_feeders(conn=None):
    """Q10 — Feeders whose connected-meter count exceeds safe load threshold."""
    return _run("""
        SELECT f.Feeder_ID, f.Load_Profile,
               COUNT(m.Meter_ID) AS meter_count,
               ROUND((0.9 * 1000 * f.Load_Profile) / 1.5) AS threshold
        FROM Feeder f
        LEFT JOIN Meter m ON f.Feeder_ID = m.Feeder_ID
        GROUP BY f.Feeder_ID, f.Load_Profile
        HAVING COUNT(m.Meter_ID) > (0.9 * 1000 * f.Load_Profile) / 1.5;
    """, conn=conn)


def maintenance_count_for_overloaded_substations(conn=None):
    """Q11 — Maintenance-schedule count for substations that contain >= 1 overloaded feeder."""
    return _run("""
        SELECT COUNT(ms.Maintenance_ID) AS maintenance_count, ms.Substation_ID
        FROM Maintenance_Schedule ms
        WHERE ms.Substation_ID IN (
            SELECT DISTINCT s.Substation_ID
            FROM Substation s
            JOIN Feeder f ON s.Substation_ID = f.Substation_ID
            WHERE f.Feeder_ID IN (
                SELECT f2.Feeder_ID
                FROM Feeder f2
                LEFT JOIN Meter m ON f2.Feeder_ID = m.Feeder_ID
                GROUP BY f2.Feeder_ID, f2.Load_Profile
                HAVING COUNT(m.Meter_ID) > (0.9 * 1000 * f2.Load_Profile) / 1.5
            )
        )
        GROUP BY ms.Substation_ID
        ORDER BY maintenance_count DESC;
    """, conn=conn)


def maintenance_teams_by_type(conn=None):
    """Q28 — Count of maintenance teams categorised by team type."""
    return _run("""
        SELECT Team_Type, COUNT(Team_ID) AS team_count
        FROM Maintenance_Team
        GROUP BY Team_Type
        ORDER BY team_count DESC;
    """, conn=conn)


def avg_salary_per_team_type(conn=None):
    """Q29 — Average total salary spent on maintenance teams, by team type."""
    return _run("""
        SELECT team_type, ROUND(AVG(team_salary)::numeric, 2) AS avg_team_salary
        FROM (
            SELECT SUM(e.Salary) AS team_salary, mt.Team_Type
            FROM Employee e
            NATURAL JOIN Maintenance_Team mt
            GROUP BY mt.Team_ID, mt.Team_Type
        ) sub
        GROUP BY team_type
        ORDER BY avg_team_salary DESC;
    """, conn=conn)


# ═══════════════════════════════════════════════════════════════════════
# 7 · REVENUE ANALYSIS
# ═══════════════════════════════════════════════════════════════════════

def unpaid_bills_over_amount(min_amount=1000, conn=None):
    """Q17 — Customers with unpaid bills exceeding a given amount."""
    return _run("""
        SELECT c.Customer_ID, c.Customer_Name,
               b.Total_Price, b.Billing_Date
        FROM Customer c
        JOIN Meter m ON c.Customer_ID = m.Customer_ID
        JOIN Bill  b ON m.Meter_ID    = b.Meter_ID
        WHERE b.Payment_Status = 'Unpaid' AND b.Total_Price > %s
        ORDER BY b.Total_Price DESC;
    """, (min_amount,), conn=conn)


def revenue_by_customer_type(year, conn=None):
    """Q20 — Total paid revenue by customer type in a given year."""
    return _run("""
        SELECT ct.Type_Name,
               SUM(b.Total_Price) AS total_revenue
        FROM Bill b
        JOIN Electricity_Rate er ON er.Rate_ID = b.Rate_ID
        JOIN Customer_Type ct    ON ct.Customer_Type_ID = er.Customer_Type_ID
        WHERE b.Payment_Status = 'Paid'
          AND DATE_PART('year', b.Billing_Date) = %s
        GROUP BY ct.Type_Name
        ORDER BY total_revenue DESC;
    """, (year,), conn=conn)


def avg_bill_by_customer_type_in_state(state="GUJARAT", conn=None):
    """Q25 — Average bill amount per customer type for a given state."""
    return _run("""
        SELECT ct.Type_Name,
               ROUND(AVG(b.Total_Price)::numeric, 2) AS avg_bill
        FROM Bill b
        NATURAL JOIN Meter m
        NATURAL JOIN (
            SELECT c.Customer_ID, c.Customer_Type_ID
            FROM Customer c
            JOIN Pin_Code pc ON c.Pin_Code = pc.Pin_Code
            WHERE pc.State = %s
        ) cust
        NATURAL JOIN Customer_Type ct
        GROUP BY ct.Type_Name
        ORDER BY avg_bill DESC;
    """, (state,), conn=conn)


# ═══════════════════════════════════════════════════════════════════════
# 8 · CONSUMPTION TREND ANALYSIS
# ═══════════════════════════════════════════════════════════════════════

def avg_rate_by_customer_type(conn=None):
    """Q14 — Average electricity rate for each customer type (all time)."""
    return _run("""
        SELECT ct.Type_Name,
               ROUND(AVG(er.Electricity_Rate)::numeric, 2) AS average_rate
        FROM Electricity_Rate er
        JOIN Customer_Type ct ON er.Customer_Type_ID = ct.Customer_Type_ID
        GROUP BY ct.Type_Name
        ORDER BY average_rate DESC;
    """, conn=conn)


def avg_consumption_per_substation_yearly(conn=None):
    """Q26a — Average energy consumption per substation per year."""
    return _run("""
        SELECT sub.Substation_ID,
               EXTRACT(YEAR FROM b.Billing_Date)::int AS year,
               ROUND(AVG(b.Total_Price / er.Electricity_Rate)::numeric, 2)
                   AS avg_consumption
        FROM Feeder f
        JOIN Substation sub      ON sub.Substation_ID = f.Substation_ID
        JOIN Meter m             ON m.Feeder_ID       = f.Feeder_ID
        JOIN Bill b              ON b.Meter_ID        = m.Meter_ID
        JOIN Electricity_Rate er ON b.Rate_ID         = er.Rate_ID
        GROUP BY sub.Substation_ID, EXTRACT(YEAR FROM b.Billing_Date)
        ORDER BY sub.Substation_ID, year;
    """, conn=conn)


def avg_consumption_for_substation_in_year(substation_id, year, conn=None):
    """Q26b — Average energy consumption for a specific substation in a given year."""
    return _run("""
        SELECT ROUND(AVG(b.Total_Price / er.Electricity_Rate)::numeric, 2)
                   AS avg_consumption
        FROM Feeder f
        JOIN Substation sub      ON sub.Substation_ID = f.Substation_ID
        JOIN Meter m             ON m.Feeder_ID       = f.Feeder_ID
        JOIN Bill b              ON b.Meter_ID        = m.Meter_ID
        JOIN Electricity_Rate er ON b.Rate_ID         = er.Rate_ID
        WHERE sub.Substation_ID = %s
          AND DATE_PART('year', b.Billing_Date) = %s;
    """, (substation_id, year), conn=conn)


def consumption_by_customer_type_yearly(conn=None):
    """Q32 — Yearly average consumption per customer type."""
    return _run("""
        SELECT er.Customer_Type_ID,
               ct.Type_Name,
               EXTRACT(YEAR FROM b.Billing_Date)::int AS year,
               ROUND(AVG(b.Total_Price / er.Electricity_Rate)::numeric, 2)
                   AS avg_consumption
        FROM Bill b
        JOIN Electricity_Rate er ON b.Rate_ID = er.Rate_ID
        JOIN Customer_Type ct    ON er.Customer_Type_ID = ct.Customer_Type_ID
        GROUP BY er.Customer_Type_ID, ct.Type_Name,
                 EXTRACT(YEAR FROM b.Billing_Date)
        ORDER BY er.Customer_Type_ID, year;
    """, conn=conn)


def consumption_trend_by_type_and_rate(conn=None):
    """Q33 — Consumption trend by customer type, electricity rate, and year."""
    return _run("""
        SELECT er.Customer_Type_ID,
               ct.Type_Name,
               er.Electricity_Rate AS rate,
               EXTRACT(YEAR FROM b.Billing_Date)::int AS year,
               ROUND(AVG(b.Total_Price / er.Electricity_Rate)::numeric, 2)
                   AS avg_consumption
        FROM Bill b
        JOIN Electricity_Rate er ON b.Rate_ID = er.Rate_ID
        JOIN Customer_Type ct    ON er.Customer_Type_ID = ct.Customer_Type_ID
        GROUP BY er.Customer_Type_ID, ct.Type_Name,
                 er.Electricity_Rate, EXTRACT(YEAR FROM b.Billing_Date)
        ORDER BY er.Customer_Type_ID, rate, year;
    """, conn=conn)


def low_consumption_pin_codes_customer_growth(threshold=100, conn=None):
    """Q35 — Year-wise customer count in pin codes whose average consumption
    per customer in any year fell below *threshold* units."""
    return _run("""
        WITH YearlyCustomerConsumption AS (
            SELECT c.Pin_Code,
                   EXTRACT(YEAR FROM b.Billing_Date)::int AS year,
                   c.Customer_ID,
                   SUM(b.Total_Price / er.Electricity_Rate) AS yearly_usage
            FROM Bill b
            JOIN Meter m             ON b.Meter_ID    = m.Meter_ID
            JOIN Customer c          ON c.Customer_ID  = m.Customer_ID
            JOIN Electricity_Rate er ON er.Rate_ID     = b.Rate_ID
            GROUP BY c.Pin_Code, EXTRACT(YEAR FROM b.Billing_Date), c.Customer_ID
        ),
        AvgConsumptionPerPin AS (
            SELECT Pin_Code, year,
                   AVG(yearly_usage) AS avg_per_customer
            FROM YearlyCustomerConsumption
            GROUP BY Pin_Code, year
            HAVING AVG(yearly_usage) < %s
        ),
        CustomerCountPerYear AS (
            SELECT c.Pin_Code,
                   EXTRACT(YEAR FROM b.Billing_Date)::int AS year,
                   COUNT(DISTINCT c.Customer_ID) AS customer_count
            FROM Bill b
            JOIN Meter m    ON b.Meter_ID   = m.Meter_ID
            JOIN Customer c ON m.Customer_ID = c.Customer_ID
            WHERE c.Pin_Code IN (SELECT Pin_Code FROM AvgConsumptionPerPin)
            GROUP BY c.Pin_Code, EXTRACT(YEAR FROM b.Billing_Date)
        )
        SELECT Pin_Code, year, customer_count
        FROM CustomerCountPerYear
        ORDER BY Pin_Code, year;
    """, (threshold,), conn=conn)