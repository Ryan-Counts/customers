import React, { useState, useMemo } from 'react';

const PAGE_SIZE_OPTIONS = [10, 15, 20];

const CustomerList = ({ customers, selectedCustomer, handleSelectCustomer }) => {
    const [search, setSearch] = useState("");    
    const [pageSize, setPageSize] = useState(PAGE_SIZE_OPTIONS[1]); // default to 15
    const [currentPage, setCurrentPage] = useState(1);
    const [sortKey, setSortKey] = useState("name");
    const [sortDir, setSortDir] = useState("1");

    const filtered = useMemo(() => {
        const q = search.toLowerCase();
        return customers.filter(c =>
            c.name?.toLowerCase().includes(q) ||
            c.primary_email?.toLowerCase().includes(q) ||
            c.company?.toLowerCase().includes(q)
        );
    }, [customers, search]);

    const sorted = useMemo(() => {
        return [...filtered].sort((a, b) => {
            let av = a[sortKey] ?? "", bv = b[sortKey] ?? "";
            if (typeof av === "string") av = av.toLowerCase();
            if (typeof bv === "string") bv = bv.toLowerCase();
            return av < bv ? -sortDir : av > bv ? sortDir : 0;
        });
    }, [filtered, sortKey, sortDir]);

    const totalPages = Math.max(1, Math.ceil(sorted.length / pageSize));
    const clampedPage = Math.min(currentPage, totalPages);
    const slice = sorted.slice((clampedPage - 1) * pageSize, clampedPage * pageSize);

    const handleSort = (key) => {
        if (key === sortKey) setSortDir(d => d * -1);
        else{
            setSortKey(key);
            setSortDir(1);
        }
        setPage(1)
    }

    const handleSearch = (e) => {
        setSearch(e.target.value);
        setPage(1);
    }

    const sortIcon = (key) => sortKey === key ? (sortDir === 1 ? "▲" : "▼") : "⇅";

    const initials = (name) => name?.split(' ').map(w => w[0]).join('').slice(0,2).toUpperCase() || "??";

    return (
        <div className="customer-list">
            <div className="list-toolbar">
                <input
                    type="text"
                    placeholder="Search customers..."
                    value={search}
                    onChange={handleSearch}
                    className="search-input"
                />
                <label className="page-size-label">
                    Show&nbsp;
                    <select value={pageSize} onChange={e => { setPageSize(Number(e.target.value)); setPage(1); }}>
                        {PAGE_SIZE_OPTIONS.map(n => <option key={n} value={n}>{n}</option>)}
                    </select>
                    &nbsp;per page
                </label>
            </div>
            <div className="table-wrap">
                <table className="customer-table">
                    <thead>
                        <tr>
                            <th onClick={() => handleSort("name")}>Name {sortIcon("name")}</th>
                            <th onClick={() => handleSort("primary_email")}>Email {sortIcon("primary_email")}</th>
                            <th onClick={() => handleSort("company")}>Company {sortIcon("company")}</th>
                            <th onClick={() => handleSort("course_count")}>Courses {sortIcon("course_count")}</th>
                            <th onClick={() => handleSort("source")}>Source {sortIcon("source")}</th>
                        </tr>
                    </thead>
                    <tbody>
                        {slice.length === 0 ? (
                            <tr><td colSpan={5} className="empty-row">No customers match your search.</td></tr>
                        ) : slice.map(customer => (
                            <tr
                                key={customer.id}
                                onClick={() => handleSelectCustomer(customer)}
                                className={selectedCustomer?.id === customer.id ? 'selected' : ''}
                            >
                                <td>
                                    <div className="name-cell">
                                        <span>{customer.name}</span>
                                    </div>
                                </td>
                                <td className="muted-cell">{customer.primary_email || '—'}</td>
                                <td>{customer.company || '—'}</td>
                                <td>
                                    <span className={`course-badge ${customer.course_count === 0 ? 'zero' : ''}`}>
                                        {customer.course_count ?? 0}
                                    </span>
                                </td>
                                <td><span className="source-tag">{customer.source}</span></td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
            <div className="list-footer">
                <span className="footer-info">
                    {sorted.length === 0 ? 'No results' :
                        `Showing ${(clampedPage - 1) * pageSize + 1}–${Math.min(clampedPage * pageSize, sorted.length)} of ${sorted.length}`}
                </span>
                <div className="pagination">
                    <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={clampedPage === 1}>‹</button>
                    {Array.from({ length: totalPages }, (_, i) => i + 1)
                        .filter(p => p === 1 || p === totalPages || Math.abs(p - clampedPage) <= 2)
                        .reduce((acc, p, i, arr) => {
                            if (i > 0 && p - arr[i - 1] > 1) acc.push('…');
                            acc.push(p);
                            return acc;
                        }, [])
                        .map((p, i) => p === '…'
                            ? <span key={`ellipsis-${i}`} className="ellipsis">…</span>
                            : <button key={p} onClick={() => setCurrentPage(p)} className={clampedPage === p ? 'active' : ''}>{p}</button>
                        )}
                    <button onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))} disabled={clampedPage === totalPages}>›</button>
                </div>
            </div>
        </div>
    );
};

export default CustomerList;