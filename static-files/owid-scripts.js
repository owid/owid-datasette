const copyToClipboard = async (text) => {
  await navigator.clipboard.writeText(text);
};

const addCopyButtonToCell = (cell, value) => {
  const copyButton = document.createElement("a");
  copyButton.className = "owid-button owid-copy-button fa fa-copy";
  copyButton.onclick = () => copyToClipboard(value);
  cell.append(copyButton);
};

const externalUrlFields = {
  "owid.charts.slug": (slug) => `https://ourworldindata.org/grapher/${slug}`,
  "owid.charts.id": (id) => `https://owid.cloud/admin/charts/${id}/edit`,
};

const addExternalUrlButtonToCell = (cell, field, value) => {
  const href = externalUrlFields[field]?.(value);

  if (!href) return;
  const externalUrlButton = document.createElement("a");
  externalUrlButton.className =
    "owid-button owid-external-url-button fa fa-external-link-alt";
  externalUrlButton.target = "_blank";
  externalUrlButton.rel = "noopener noreferrer";
  externalUrlButton.href = href;
  cell.appendChild(externalUrlButton);
};

let databaseName;
let tableName;
const body = document.body;
body.classList.forEach((className) => {
  if (className.startsWith("db-")) databaseName = className.replace("db-", "");
  else if (className.startsWith("table-"))
    tableName = className.replace("table-", "");
});

const cells = document.querySelectorAll("table.rows-and-columns td");
cells.forEach((cell) => {
  const value = cell.innerText;
  if (!value) return;

  addCopyButtonToCell(cell, value);

  let colName;
  cell.classList.forEach((className) => {
    if (className.startsWith("col-")) colName = className.replace("col-", "");
  });

  if (databaseName && tableName && colName) {
    const field = `${databaseName}.${tableName}.${colName}`;
    addExternalUrlButtonToCell(cell, field, value);
  }
});
