// import logo from './logo.svg';
import { Route, Switch } from "react-router-dom";
import "./App.css";
import Courses from "./components/courses";
import Course from "./components/course";
import SubTopic from "./components/subtopic";

function Reload() {
  return <div>reload</div>;
}

function App() {
  return (
    <div className="App p-3">
      <Switch>
        <Route
          path="/courses/s/:coursekey/:topickey/:subtopickey"
          exact
          component={SubTopic}
        ></Route>
        <Route path="/courses/s/:coursekey" exact component={Course}></Route>
        <Route path="/courses/s" exact component={Courses}></Route>
        <Route path="" component={Reload}></Route>
      </Switch>
    </div>
  );
}

export default App;
