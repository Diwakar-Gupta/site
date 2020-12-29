import React from "react";
import { Breadcrumb } from "react-bootstrap";
import { NavLink } from "react-router-dom";
// import { FontAwesomeIcon } from "@fortawesome/react-fontawesome";
// import { faHome, faRefresh } from "@fortawesome/free-solid-svg-icons";
// import {faRefresh} from '@fortawesome/free-regular-svg-icons';
import { FaHome } from "react-icons/fa";

export default function BreadCrumb(props) {
  props = props || {};
  console.log(props);
  return (
    <Breadcrumb>
      <Breadcrumb.Item href="/">
        <FaHome size={18} />
      </Breadcrumb.Item>
      <Breadcrumb.Item linkAs={NavLink} linkProps={{ to: "/courses/s/" }}>
        Courses
      </Breadcrumb.Item>

      {props.coursename && (
        <Breadcrumb.Item
          linkAs={NavLink}
          linkProps={{ to: `/courses/s/${props.coursekey}` }}
        >
          {props.coursename}
        </Breadcrumb.Item>
      )}

      {props.subtopicname && (
        <Breadcrumb.Item linkAs={NavLink} linkProps={{ to: props.subtopicurl }}>
          {props.subtopicname}
        </Breadcrumb.Item>
      )}
    </Breadcrumb>
  );
}
