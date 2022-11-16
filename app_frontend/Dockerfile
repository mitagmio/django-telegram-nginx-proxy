FROM node:18.12.1 as build

# RUN mkdir /root/.ssh/

# RUN touch /root/.ssh/known_hosts
# RUN ssh-keyscan -H github.com >> ~/.ssh/known_hosts

RUN apt update && apt install git

RUN git clone https://github.com/artem-gladkov/om-dao.git

WORKDIR /om-dao

RUN npm install

RUN npm run build

FROM nginx
COPY ./nginx/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /om-dao/build /usr/share/nginx/html