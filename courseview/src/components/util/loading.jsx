import React from "react";
import Spinner from "react-bootstrap/Spinner";

export default function loading() {
  return (
    <div>
      <Spinner
        key="primary"
        style={{
          "marginLeft": "49%",
          "marginRight": "49%",
          "marginTop": "4rem",
        }}
        animation="border"
        variant="primary"
      />
    </div>
  );
}

/*

{[
         "primary",
         "secondary",
         "success",
         "danger",
         "warning",
         "info",
         "dark",
       ].map((typ) => (
         <Spinner key={typ} animation="border" variant={typ} />
       ))}

       */
