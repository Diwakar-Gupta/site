import React, { Component } from "react";
import axios from "axios";
import { NavLink, Link } from "react-router-dom";
import Loading from "./loading";
import {
  Button,
  Card,
  CardColumns,
  Breadcrumb,
  Col,
  Row,
} from "react-bootstrap";

export default class Courses extends Component {
  state = {
    loading: false,
    error: "",
    courses: [],
  };

  componentDidMount() {
    this.fetchCourses();
  }

  fetchCourses = () => {
    this.setState({
      loading: true,
      error: "",
    });
    axios
      .get("/courses/api/courses/")
      .then((res) => {
        console.log(res.data);
        this.setState({
          loading: false,
          courses: res.data,
          error: "",
        });
      })
      .catch((err) => {
        if (err.response) {
          if (err.response.status === 404) {
            this.setState({ loading: false, error: "Resourse not available" });
          } else {
            this.setState({ loading: false, error: err.response.data });
          }
        } else {
          this.setState({ loading: false, error: err.message });
        }
      });
  };

  enrollTo = (coursekey) => {
    axios
      .get(`/courses/api/course/${coursekey}/enroll`)
      .then((res) => {
        console.log(res)
        this.fetchCourses()
      })
      .catch((err) => {
        console.log(err)
        this.setState({
          error:  err.responst.status===403?err.responst.data : 'some thing wrong happend'
        })
        setTimeout(() => {
          this.setState({
            error:''
          })
        }, 2000);
      });
  };

  renderCourse = (course) => {
    return (
      <Card key={course.key}>
        <Card.Body>
          <Card.Title>{course.name}</Card.Title>
          <Card.Text
            className="text-muted"
            style={{ minHeight: "1rem" }}
          ></Card.Text>
          {course.enrolled ? (
            <Button variant="primary" to={`/courses/s/${course.key}`} as={Link}>
              Continue Course
            </Button>
          ) : (
            <Row>
              <Col>
                <Button
                  variant="primary"
                  to={`/courses/s/${course.key}`}
                  as={Link}
                >
                  View
                </Button>
              </Col>
              <Col>
                <Button variant="primary" onClick={()=>{this.enrollTo(course.key)}}>
                  Enroll
                </Button>
              </Col>
            </Row>
          )}
        </Card.Body>
      </Card>
    );
  };

  render() {
    return (
      <div>
        <Breadcrumb>
          <Breadcrumb.Item linkAs={NavLink} linkProps={{ to: "/courses/s" }}>
            Courses
          </Breadcrumb.Item>
        </Breadcrumb>
        {this.state.loading ? (
          <div>
            <Loading />
          </div>
        ) : (
          <CardColumns>
            {this.state.error ? (
              <div className="text-center">{this.state.error}</div>
            ) : this.state.courses.length === 0 ? (
              <div className="text-center">{"No Course available for u"}</div>
            ) : this.state.courses.length === 0 ? (
              <div>No Course For U Now</div>
            ) : (
              this.state.courses.map(this.renderCourse)
            )}
          </CardColumns>
        )}
      </div>
    );
  }
}
